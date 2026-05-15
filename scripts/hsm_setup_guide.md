# 🔐 Guia de Configuração de HSM para Arkhe Cathedral

## Pré-requisitos

### Hardware/Software
- HSM compatível com PKCS#11 v2.40+ ou API nativa
- Windows 10/11 x64 ou Windows Server 2019+
- Windows SDK 10.0+ (para signtool)
- PowerShell 7.0+ para scripts de automação

### Certificados
- Certificado de código assinado por CA raiz confiável
- Cadeia de certificados completa (root → intermediate → code-signing)
- Certificado válido para "Kernel Mode Code Signing" (se aplicável)

## Configuração por Provedor

### Thales nCipher
```bash
# 1. Instalar nCipher PKCS#11 toolkit
# 2. Configurar token e slot
nfast-token-admin --list-tokens

# 3. Gerar par de chaves no HSM
nfast-key-admin --generate --label arkhe-cathedral-production --keytype rsa --keysize 4096

# 4. Importar certificado para o token
nfast-cert-admin --import --label arkhe-cathedral-production --cert arkhe-code-signing.crt

# 5. Configurar variáveis de ambiente
export CKR_TOKEN_LABEL="arkhe-hsm-token"
export HSM_PIN="****"  # Via secure storage, não em plaintext
```

### AWS CloudHSM
```bash
# 1. Configurar cluster CloudHSM via AWS Console/CLI
aws cloudhsmv2 create-cluster --source-backup-identifier <backup-id>

# 2. Instalar CloudHSM client
sudo yum install cloudhsm-client

# 3. Inicializar cliente
cloudhsm-client configure --cluster-id <cluster-id>

# 4. Gerar chave no HSM
cloudhsm-client key generate --label arkhe-cathedral-production --algorithm RSA --size 4096

# 5. Configurar CSP para Windows (se assinando no Windows)
# Usar AWS-provided CSP ou configurar PKCS#11 bridge
```

### Azure Dedicated HSM
```powershell
# 1. Provisionar Dedicated HSM via Azure Portal/CLI
az dedicated-hsm create `
  --name arkhe-hsm-prod `
  --resource-group arkhe-rg `
  --location westus2 `
  --sku "SafeNet Luna Network HSM A79"

# 2. Configurar rede e acesso
az network vnet subnet update `
  --name hsm-subnet `
  --vnet-name arkhe-vnet `
  --resource-group arkhe-rg `
  --service-endpoints "Microsoft.AzureActiveDirectory"

# 3. Instalar SafeNet Authentication Client
# 4. Configurar PKCS#11 module path no Windows registry
```

## Configuração do Windows para PKCS#11

### Registrar CSP/PKCS#11 Provider
```powershell
# Registrar provider PKCS#11 no CryptoAPI
$providerName = "ARKHE PKCS#11 Provider"
$pkcs11Lib = "C:\Program Files\HSM\lib\pkcs11.dll"

# Via registry (requer admin)
New-ItemProperty -Path "HKLM:\SOFTWARE\Microsoft\Cryptography\Defaults\Provider\$providerName" `
  -Name "Image Path" -Value $pkcs11Lib -PropertyType String -Force

# Configurar tipos de chave suportados
New-ItemProperty -Path "HKLM:\SOFTWARE\Microsoft\Cryptography\Defaults\Provider\$providerName" `
  -Name "Signature" -Value "0x0001" -PropertyType DWORD -Force  # RSA
```

### Configurar signtool para HSM
```powershell
# Criar arquivo de configuração para signtool
$signConfig = @"
{
  "provider": "ARKHE PKCS#11 Provider",
  "keyContainer": "arkhe-cathedral-production",
  "certificateThumbprint": "A1B2C3D4E5F6...",
  "timestampServer": "http://timestamp.digicert.com",
  "hashAlgorithm": "SHA3_256"
}
"@
$signConfig | Out-File -FilePath "C:\arkhe\sign_config.json" -Encoding UTF8

# Assinar usando configuração
signtool sign /csp "ARKHE PKCS#11 Provider" /kc "arkhe-cathedral-production" `
  /tr http://timestamp.digicert.com /td SHA3_256 /fd SHA3_256 `
  /d "Arkhe Cathedral Kernel" catedral.sys
```

## Validação Pós-Assinatura

### Verificar assinatura
```powershell
# Verificar arquivo assinado
signtool verify /pa /v catedral_signed.sys

# Verificar catálogo
Test-FileCatalog -Path "C:\Windows\System32\drivers" `
  -CatalogFilePath "catedral_signed.cat" -Detailed

# Verificar via PowerShell
$cert = Get-AuthenticodeSignature catedral_signed.sys
if ($cert.Status -eq 'Valid') {
    Write-Host "✅ Assinatura válida"
    Write-Host "   Signer: $($cert.SignerCertificate.Subject)"
    Write-Host "   Valid from: $($cert.SignerCertificate.NotBefore)"
    Write-Host "   Valid to: $($cert.SignerCertificate.NotAfter)"
}
```

### Auditoria de uso do HSM
```bash
# Thales: logs de uso de chave
nfast-audit --query --key-label arkhe-cathedral-production --since "2026-01-01"

# AWS CloudHSM: CloudWatch logs
aws logs filter-log-events `
  --log-group-name /aws/cloudhsm/audit `
  --filter-pattern "arkhe-cathedral-production"

# Azure: Monitor logs via Azure Monitor
# Configurar diagnostic settings para Dedicated HSM
```

## Segurança e Compliance

### Proteção da chave HSM
- Nunca exportar chave privada do HSM
- Usar autenticação multifator para acesso administrativo
- Habilitar logging de todas as operações criptográficas
- Implementar quórum para operações críticas (M of N)

### Rotação de certificados
- Planejar renovação 60 dias antes da expiração
- Manter certificado anterior válido durante transição
- Atualizar catálogo e re-assinar binários com novo certificado

### Backup e recuperação
- Backup regular do HSM (se suportado pelo provedor)
- Documentar procedimento de recuperação de desastre
- Testar restore periodicamente em ambiente isolado

## Troubleshooting

### Erro: "Provider not found"
```powershell
# Verificar providers registrados
Get-ChildItem "HKLM:\SOFTWARE\Microsoft\Cryptography\Defaults\Provider"

# Re-registrar provider
certutil -csp "ARKHE PKCS#11 Provider" -key
```

### Erro: "Key not found"
```bash
# Listar chaves no HSM
# Thales:
nfast-key-admin --list-keys

# AWS CloudHSM:
cloudhsm-client key list --label-prefix arkhe
```

### Erro: "Timestamp failed"
```powershell
# Verificar conectividade com timestamp server
Test-NetConnection timestamp.digicert.com -Port 80

# Tentar servidor alternativo
signtool sign /tr http://timestamp.entrust.net/TSS/RFC3161sha2TS /td SHA3_256 ...
```

## Suporte

- Documentação completa: https://arkhe.org/docs/hsm-signing
- Suporte técnico: security@arkhe.org
- Emergência de segurança: security-emergency@arkhe.org (PGP: 0xARKHE-SEC)
