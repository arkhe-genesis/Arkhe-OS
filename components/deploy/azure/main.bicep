targetScope = 'resourceGroup'

@description('Nome base para todos os recursos. Ex: arkhe')
param baseName string = 'arkhe'

@description('Localização dos recursos. Padrão: Brazil South (baixa latência para o Tecelão)')
param location string = 'brazilsouth'

@description('Nome do utilizador administrador para o cluster AKS.')
param aksAdminUsername string = 'arkheAdmin'

@description('Chave SSH pública para acesso aos nós do AKS.')
param sshPublicKey string

// 1. Azure Container Registry (ACR) - O Berço das Imagens
module acr 'br/public:avm/res/container-registry/registry:0.1.0' = {
  name: 'acrDeployment'
  params: {
    name: '${baseName}acr${uniqueString(resourceGroup().id)}'
    location: location
    sku: 'Basic'
    adminUserEnabled: false
  }
}

// 2. Azure Kubernetes Service (AKS) - A Forja dos Agentes
module aks 'br/public:avm/res/container-service/managed-cluster:0.1.0' = {
  name: 'aksDeployment'
  params: {
    name: '${baseName}-aks'
    location: location
    dnsPrefix: '${baseName}-aks'
    agentCount: 2
    agentVMSize: 'Standard_B2s' // Suficiente para Dev/Test
    osDiskSizeGB: 30
    enableRBAC: true
    networkPlugin: 'azure'
    networkPolicy: 'azure'
    outboundType: 'loadBalancer'
    linuxAdminUsername: aksAdminUsername
    sshPublicKey: sshPublicKey
  }
}

// 3. Azure Service Bus - O Sistema Nervoso
module serviceBus 'br/public:avm/res/service-bus/namespace:0.1.0' = {
  name: 'sbDeployment'
  params: {
    name: '${baseName}-sb-${uniqueString(resourceGroup().id)}'
    location: location
    sku: 'Standard'
    topics: [
      { name: 'editorial-pitches' }
      { name: 'task-completed' }
    ]
  }
}

// 4. Azure Cosmos DB (MongoDB vCore) - O Cristal de Memória
module cosmos 'br/public:avm/res/cosmos-db/account:0.1.0' = {
  name: 'cosmosDeployment'
  params: {
    name: '${baseName}-cosmos-${uniqueString(resourceGroup().id)}'
    location: location
    kind: 'MongoDB'
    capabilities: [{ name: 'EnableMongo' } { name: 'EnableMongoRoleBasedAccessControl' }]
    apiProperties: {
      serverVersion: '4.2'
    }
    locations: [
      {
        locationName: location
        failoverPriority: 0
        isZoneRedundant: false
      }
    ]
  }
}

// 5. Azure OpenAI Service - O Oráculo dos LLMs
module openAI 'br/public:avm/res/cognitive-services/account:0.1.0' = {
  name: 'openAIDeployment'
  params: {
    name: '${baseName}-openai-${uniqueString(resourceGroup().id)}'
    location: 'eastus' // OpenAI pode ter restrição de região
    kind: 'OpenAI'
    sku: 'S0'
    deployments: [
      { name: 'gpt-4o', model: { format: 'OpenAI', name: 'gpt-4o', version: '2024-05-13' }, sku: { name: 'Standard', capacity: 10 } }
      { name: 'text-embedding-3-large', model: { format: 'OpenAI', name: 'text-embedding-3-large', version: '1' }, sku: { name: 'Standard', capacity: 10 } }
    ]
  }
}

// 6. Azure Key Vault - O Cofre dos Segredos
module keyVault 'br/public:avm/res/key-vault/vault:0.1.0' = {
  name: 'kvDeployment'
  params: {
    name: '${baseName}-kv-${uniqueString(resourceGroup().id)}'
    location: location
    enableRbacAuthorization: true
    enableSoftDelete: true
    sku: 'standard'
  }
}

// Saídas para referência nos pipelines de CI/CD
output acrLoginServer string = acr.outputs.loginServer
output aksClusterName string = aks.outputs.name
output cosmosEndpoint string = cosmos.outputs.endpoint
output openAIEndpoint string = openAI.outputs.endpoint
output keyVaultUri string = keyVault.outputs.uri
