// hsm_windows_integration.cs — Substrato 199.1: HSM PQC para Windows
// Canon: ∞.Ω.∇+++.199.1.hsm
// Assina execuções system32 com chaves enraizadas em HSM (Thales/Utimaco/AWS CloudHSM)

using System;
using System.Diagnostics;
using System.Security.Cryptography;
using System.Text;
using System.Threading.Tasks;
using Microsoft.Win32.SafeHandles;

namespace Arkhe.Windows.HSM
{
    /// <summary>
    /// Assinador PQC com HSM para execuções system32.
    /// Chaves privadas NUNCA saem do módulo de hardware.
    /// </summary>
    public class HSMProductionSigner : IDisposable
    {
        private readonly SafeNCryptKeyHandle _hsmKeyHandle;
        private readonly string _algorithm; // "Dilithium3", "Kyber1024"
        private readonly string _keyLabel;
        private bool _disposed;

        public HSMProductionSigner(string hsmProvider, string keyLabel, string algorithm = "Dilithium3")
        {
            _keyLabel = keyLabel;
            _algorithm = algorithm;

            // Conectar ao HSM via CNG (Cryptographic Next Generation)
            _hsmKeyHandle = OpenHSMKey(hsmProvider, keyLabel);
        }

        private SafeNCryptKeyHandle OpenHSMKey(string provider, string keyLabel)
        {
            // Em produção: usar NCryptOpenStorageProvider + NCryptOpenKey
            // Aqui: mock para demonstração
            return new SafeNCryptKeyHandle(IntPtr.Zero, true);
        }

        /// <summary>
        /// Assina hash de execução system32 dentro do HSM.
        /// </summary>
        public async Task<HSMSigningResult> SignExecutionAsync(
            string executablePath,
            byte[] contentHash,
            ExecutionMetadata metadata)
        {
            var stopwatch = Stopwatch.StartNew();

            try
            {
                // 1. Preparar dados para assinatura (SHA3-256 já calculado)
                var signingData = PrepareSigningData(contentHash, metadata);

                // 2. Assinar dentro do HSM (chave nunca sai do hardware)
                var signature = await SignWithHSMAsync(signingData);

                stopwatch.Stop();

                return new HSMSigningResult
                {
                    Success = true,
                    Algorithm = _algorithm,
                    SignatureHex = Convert.ToHexString(signature),
                    SignatureSizeBytes = signature.Length,
                    SigningTimeMs = stopwatch.ElapsedMilliseconds,
                    HSMKeyId = _keyLabel,
                    ExecutionHash = Convert.ToHexString(contentHash),
                    Timestamp = DateTimeOffset.UtcNow.ToUnixTimeSeconds()
                };
            }
            catch (Exception ex)
            {
                return new HSMSigningResult
                {
                    Success = false,
                    Algorithm = _algorithm,
                    ErrorMessage = ex.Message,
                    Timestamp = DateTimeOffset.UtcNow.ToUnixTimeSeconds()
                };
            }
        }

        private byte[] PrepareSigningData(byte[] contentHash, ExecutionMetadata metadata)
        {
            // Estrutura de dados para assinatura: hash + metadados + nonce
            using var ms = new System.IO.MemoryStream();
            ms.Write(contentHash, 0, contentHash.Length);
            ms.Write(Encoding.UTF8.GetBytes(metadata.ExecutablePath));
            ms.Write(BitConverter.GetBytes(metadata.Timestamp));
            ms.Write(Guid.NewGuid().ToByteArray()); // Nonce anti-replay
            return ms.ToArray();
        }

        private async Task<byte[]> SignWithHSMAsync(byte[] data)
        {
            // Em produção: usar NCryptSignHash com mecanismo PQC
            // Mock: retornar hash "assinado" para demonstração
            using var sha3 = SHA3_256.Create();
            var signed = sha3.ComputeHash(data);
            await Task.Yield(); // Simular latência HSM
            return signed;
        }

        /// <summary>
        /// Verifica assinatura PQC de execução system32.
        /// </summary>
        public async Task<bool> VerifyExecutionAsync(
            byte[] contentHash,
            byte[] signature,
            byte[] publicKey,
            ExecutionMetadata metadata)
        {
            var signingData = PrepareSigningData(contentHash, metadata);

            // Em produção: usar NCryptVerifySignature com chave pública PQC
            // Mock: verificação simplificada
            using var sha3 = SHA3_256.Create();
            var expected = sha3.ComputeHash(signingData);

            await Task.Yield();
            return signature.AsSpan().SequenceEqual(expected.AsSpan());
        }

        /// <summary>
        /// Rotação de chave PQC no HSM com período de sobreposição.
        /// </summary>
        public async Task<KeyRotationResult> RotateKeyAsync(
            string newKeyLabel,
            int overlapHours = 24)
        {
            // Em produção: usar API do HSM para gerar novo par de chaves
            // Mock: simular rotação
            var result = new KeyRotationResult
            {
                OldKeyLabel = _keyLabel,
                NewKeyLabel = newKeyLabel,
                OverlapUntil = DateTimeOffset.UtcNow.AddHours(overlapHours).ToUnixTimeSeconds(),
                Algorithm = _algorithm,
                Timestamp = DateTimeOffset.UtcNow.ToUnixTimeSeconds()
            };

            await Task.Yield();
            return result;
        }

        protected virtual void Dispose(bool disposing)
        {
            if (!_disposed)
            {
                if (disposing)
                {
                    _hsmKeyHandle?.Dispose();
                }
                _disposed = true;
            }
        }

        public void Dispose()
        {
            Dispose(true);
            GC.SuppressFinalize(this);
        }
    }

    public class ExecutionMetadata
    {
        public string ExecutablePath { get; set; }
        public string[] Arguments { get; set; }
        public long Timestamp { get; set; }
        public string UserSid { get; set; }
        public string SessionId { get; set; }
    }

    public class HSMSigningResult
    {
        public bool Success { get; set; }
        public string Algorithm { get; set; }
        public string SignatureHex { get; set; }
        public int SignatureSizeBytes { get; set; }
        public long SigningTimeMs { get; set; }
        public string HSMKeyId { get; set; }
        public string ExecutionHash { get; set; }
        public long Timestamp { get; set; }
        public string ErrorMessage { get; set; }
    }

    public class KeyRotationResult
    {
        public string OldKeyLabel { get; set; }
        public string NewKeyLabel { get; set; }
        public long OverlapUntil { get; set; }
        public string Algorithm { get; set; }
        public long Timestamp { get; set; }
    }

    // Mock SHA3-256 para demonstração
    internal class SHA3_256 : HashAlgorithm
    {
        public static new SHA3_256 Create() => new SHA3_256();
        protected override void HashCore(byte[] array, int ibStart, int cbSize) { }
        protected override byte[] HashFinal() => new byte[32];
        public override void Initialize() { }
    }
}