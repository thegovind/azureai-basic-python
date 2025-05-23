#!/bin/bash

# Define the .env file path
ENV_FILE_PATH="src/.env"

# Clear the contents of the .env file
> $ENV_FILE_PATH

echo "AZURE_AIPROJECT_CONNECTION_STRING=$(azd env get-value AZURE_AIPROJECT_CONNECTION_STRING)" >> $ENV_FILE_PATH
echo "AZURE_AI_CHAT_DEPLOYMENT_NAME=$(azd env get-value AZURE_AI_CHAT_DEPLOYMENT_NAME)" >> $ENV_FILE_PATH
echo "AZURE_TENANT_ID=$(azd env get-value AZURE_TENANT_ID)" >> $ENV_FILE_PATH
echo "AZURE_AI_EMBED_DEPLOYMENT_NAME=$(azd env get-value AZURE_AI_EMBED_DEPLOYMENT_NAME)" >> $ENV_FILE_PATH
echo "AZURE_AI_EMBED_DIMENSIONS=$(azd env get-value AZURE_AI_EMBED_DIMENSIONS)" >> $ENV_FILE_PATH
echo "AZURE_AI_SEARCH_INDEX_NAME=$(azd env get-value AZURE_AI_SEARCH_INDEX_NAME)" >> $ENV_FILE_PATH
echo "AZURE_AI_SEARCH_ENDPOINT=$(azd env get-value AZURE_AI_SEARCH_ENDPOINT)" >> $ENV_FILE_PATH

echo "Web app URL:"
echo -e "\033[0;36m $(azd env get-value SERVICE_API_URI)"
exit 0