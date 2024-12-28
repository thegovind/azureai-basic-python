from flask import Flask, render_template, request, Response, stream_with_context
import os
from azure.ai.projects import AIProjectClient
from azure.identity import DefaultAzureCredential
import logging
import json
import sys
from werkzeug.middleware.proxy_fix import ProxyFix

# Set up logging with more detail
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

app = Flask(__name__)
# ProxyFix helps fix certain proxy headers when your app is behind a proxy (e.g. Azure App Service)
app.wsgi_app = ProxyFix(app.wsgi_app, x_proto=1, x_host=1)

def check_environment():
    """
    Ensures that the required environment variables are set.
    If any are missing, log an error and exit.
    """
    required_vars = [
        "AZURE_AIPROJECT_CONNECTION_STRING",
        "AZURE_AI_CHAT_DEPLOYMENT_NAME"
    ]
    missing = [var for var in required_vars if not os.getenv(var)]
    if missing:
        logger.error(f"Missing required environment variables: {missing}")
        sys.exit(1)

# Initialize at startup
try:
    check_environment()
    logger.info("Initializing AI client...")

    # Create an AIProjectClient from the environment's connection string,
    # using DefaultAzureCredential to authenticate via a chain of credentials
    project = AIProjectClient.from_connection_string(
        conn_str=os.environ["AZURE_AIPROJECT_CONNECTION_STRING"],
        credential=DefaultAzureCredential()
    )
    logger.info("AI client initialized successfully")
except Exception as e:
    logger.error(f"Failed to initialize application: {str(e)}", exc_info=True)
    sys.exit(1)

@app.route("/")
def index():
    """
    Renders the main page with the chat UI.
    """
    logger.info("Serving index page")
    return render_template("index.html")

@app.route("/chat/stream", methods=["POST"])
def chat():
    """
    Endpoint that streams chat responses line by line in JSON.
    The front-end library will read each line and parse it as JSON.
    """
    try:
        logger.info("Received chat request")

        # Get the messages array from JSON in the request
        messages = request.json.get('messages', [])
        logger.debug(f"Messages received: {messages}")

        # Get a chat completions client from the AIProjectClient
        chat_client = project.inference.get_chat_completions_client()

        def generate():
            """
            Generator function to stream chat responses chunk by chunk.
            Each chunk is returned as a single line of JSON (no SSE prefix).
            """
            try:
                # Request streaming chat completions
                response = chat_client.complete(
                    messages=messages,
                    model=os.environ["AZURE_AI_CHAT_DEPLOYMENT_NAME"],
                    stream=True
                )

                # Iterate through chunks (partial responses)
                for chunk in response:
                    logger.debug(f"Chunk received: {chunk}")

                    # Check if the chunk has 'choices', which contain the token deltas
                    if hasattr(chunk, 'choices') and chunk.choices:
                        choice = chunk.choices[0]
                        if hasattr(choice, 'delta'):
                            # Skip system messages and empty content
                            if not choice.delta.content:
                                continue

                            # Convert any datetime fields to ISO format so they're JSON-serializable
                            response_data = {
                                "id": getattr(chunk, "id", None),
                                "created": chunk.created.isoformat() if chunk.created else None,
                                "model": getattr(chunk, "model", None),
                                "delta": {
                                    "content": choice.delta.content
                                }
                            }

                            # Yield raw JSON (line-delimited); no "data:" prefix
                            yield json.dumps(response_data) + "\n"

            except Exception as e:
                # If an error occurs, log it and send an error message as JSON
                logger.error(f"Error in chat generation: {str(e)}", exc_info=True)
                error_response = {"error": str(e)}
                yield json.dumps(error_response) + "\n"

        # Return a streaming response with line-delimited JSON
        return Response(
            stream_with_context(generate()),
            content_type="text/plain",  # Using plain text to stream multiple JSON objects line by line
            headers={
                'Cache-Control': 'no-cache',
                'Connection': 'keep-alive',
                # 'X-Accel-Buffering': 'no' is optional; it helps with immediate streaming in some proxies
                'X-Accel-Buffering': 'no'
            }
        )

    except Exception as e:
        logger.error(f"Error in chat endpoint: {str(e)}", exc_info=True)
        return {"error": str(e)}, 500

@app.route("/health")
def health():
    """
    Simple health check endpoint that tries to create a chat completions client.
    """
    try:
        # If this succeeds, we consider the service healthy
        chat_client = project.inference.get_chat_completions_client()
        logger.debug("Health check - AI client test passed")
        return {
            "status": "healthy",
            "checks": {
                "ai_client": "ok"
            }
        }, 200
    except Exception as e:
        logger.error(f"Health check failed: {str(e)}", exc_info=True)
        return {
            "status": "unhealthy",
            "error": str(e)
        }, 500

if __name__ == "__main__":
    logger.info("Starting Flask app on port 50505...")
    app.run(host="0.0.0.0", port=50505, debug=True)
else:
    # If running under a WSGI server like gunicorn, inherit its log handlers
    gunicorn_logger = logging.getLogger('gunicorn.error')
    app.logger.handlers = gunicorn_logger.handlers
    app.logger.setLevel(gunicorn_logger.level)
