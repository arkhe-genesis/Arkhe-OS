# Compilar como single-file executável
dotnet publish Arkhe.Cli -c Release -r win-x64 --self-contained true -p:PublishSingleFile=true -o ./publish

# Assinar com certificado de código (Code Signing)
signtool sign /fd SHA256 /a /tr http://timestamp.digicert.com /td SHA256 ./publish/arkhe.exe

# Verificar assinatura
signtool verify /pa ./publish/arkhe.exe
