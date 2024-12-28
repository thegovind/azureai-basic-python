param name string
param location string = resourceGroup().location
param tags object = {}
param identityName string
param containerAppsEnvironmentName string
param containerRegistryName string
param projectConnectionString string
param chatDeploymentName string
param exists bool = false

resource identity 'Microsoft.ManagedIdentity/userAssignedIdentities@2023-01-31' = {
  name: identityName
  location: location
}

resource containerAppsEnvironment 'Microsoft.App/managedEnvironments@2023-05-01' existing = {
  name: containerAppsEnvironmentName
}

resource containerRegistry 'Microsoft.ContainerRegistry/registries@2023-07-01' existing = {
  name: containerRegistryName
}

resource app 'Microsoft.App/containerApps@2023-05-01' = {
  name: name
  location: location
  tags: tags
  identity: {
    type: 'UserAssigned'
    userAssignedIdentities: {
      '${identity.id}': {}
    }
  }
  properties: {
    managedEnvironmentId: containerAppsEnvironment.id
    configuration: {
      ingress: {
        external: true
        targetPort: 80
        allowInsecure: false
        traffic: [
          {
            latestRevision: true
            weight: 100
          }
        ]
      }
      registries: [
        {
          server: containerRegistry.properties.loginServer
          identity: identity.id
        }
      ]
    }
    template: {
      containers: [
        {
          name: 'main'
          image: exists ? 'nginx:latest' : '${containerRegistry.properties.loginServer}/api:latest'
          env: [
            {
              name: 'AZURE_AIPROJECT_CONNECTION_STRING'
              value: projectConnectionString
            }
            {
              name: 'AZURE_AI_CHAT_DEPLOYMENT_NAME'
              value: chatDeploymentName
            }
          ]
        }
      ]
      scale: {
        minReplicas: 1
        maxReplicas: 1
      }
    }
    probes: [
      {
        type: 'Startup'
        httpGet: {
          path: '/health'
          port: 80
        }
        initialDelaySeconds: 10
        periodSeconds: 30
      }
    ]
  }
}

output SERVICE_API_URI string = app.properties.configuration.ingress.fqdn
output SERVICE_API_NAME string = app.name
output SERVICE_API_IDENTITY_PRINCIPAL_ID string = identity.properties.principalId
output SERVICE_API_IMAGE_NAME string = '${containerRegistry.properties.loginServer}/api:latest'
