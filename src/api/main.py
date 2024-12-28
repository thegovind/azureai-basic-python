import contextlib
import logging
import os
import pathlib
from typing import Union

import fastapi
from azure.ai.projects.aio import AIProjectClient
from azure.ai.inference.prompts import PromptTemplate
from azure.identity import AzureDeveloperCliCredential, ManagedIdentityCredential
from dotenv import load_dotenv
from fastapi.staticfiles import StaticFiles

from .shared import globals

logger = logging.getLogger("azureaiapp")
logger.setLevel(logging.INFO)


@contextlib.asynccontextmanager
async def lifespan(app: fastapi.FastAPI):
    """
    Context manager controlling the app's lifespan. This is where we create 
    our AIProjectClient, chat client, etc., and store them in a global dictionary.
    """

    # Decide which credential to use: AzureDeveloperCliCredential or ManagedIdentityCredential
    if not os.getenv("RUNNING_IN_PRODUCTION"):
        if tenant_id := os.getenv("AZURE_TENANT_ID"):
            logger.info("Using AzureDeveloperCliCredential with tenant_id %s", tenant_id)
            azure_credential = AzureDeveloperCliCredential(tenant_id=tenant_id)
        else:
            logger.info("Using AzureDeveloperCliCredential")
            azure_credential = AzureDeveloperCliCredential()
    else:
        user_identity_client_id = os.getenv("AZURE_CLIENT_ID")
        logger.info("Using ManagedIdentityCredential with client_id %s", user_identity_client_id)
        azure_credential = ManagedIdentityCredential(client_id=user_identity_client_id)

    # Create AIProjectClient from the connection string
    project = AIProjectClient.from_connection_string(
        credential=azure_credential,
        conn_str=os.environ["AZURE_AIPROJECT_CONNECTION_STRING"],
    )

    # Create an async chat client
    chat = await project.inference.get_chat_completions_client()

    # Load a prompt template (if you need it)
    prompt = PromptTemplate.from_prompty(pathlib.Path(__file__).parent.resolve() / "prompt.prompty")

    # Store objects globally so routes.py can access them
    globals["project"] = project
    globals["chat"] = chat
    globals["prompt"] = prompt
    globals["chat_model"] = os.environ["AZURE_AI_CHAT_DEPLOYMENT_NAME"]

    # Yield control back to FastAPI until shutdown
    yield

    # Cleanup on shutdown
    await project.close()
    await chat.close()


def create_app() -> fastapi.FastAPI:
    """
    Creates and configures the FastAPI app. Mounts 'static' folder, includes routes, etc.
    """
    # Load environment variables if not in production
    if not os.getenv("RUNNING_IN_PRODUCTION"):
        logger.info("Loading .env file")
        load_dotenv(override=True)

    # Create the FastAPI instance with our custom lifespan
    app = fastapi.FastAPI(lifespan=lifespan)

    # Mount static files (CSS, JS, images) at /static
    app.mount("/static", StaticFiles(directory="api/static"), name="static")

    # Include our routes from routes.py
    from . import routes  # noqa
    app.include_router(routes.router)

    return app
