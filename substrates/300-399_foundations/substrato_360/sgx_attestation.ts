import { verifyAttestation } from "@piplabs/cdr-sdk";
import { hexToBytes } from "viem";

export class SGXAttestationValidator {
  // Canonical MRENCLAVE values
  private canonicalSeals = [
    "ce189f7f95fe5eb26dda1f3a93e61116a22d5729948ff5a125e64a2e1b881585", // 359 Canonical Seal
    "2600000000000000000000000000000000000000000000000000000000000260", // 260 Bioluminescent
    "2610000000000000000000000000000000000000000000000000000000000261", // 261
    "2630000000000000000000000000000000000000000000000000000000000263"  // 263
  ];

  public async validateEnclave(attestationHex: `0x${string}`): Promise<boolean> {
    try {
      const attestationBytes = hexToBytes(attestationHex);

      // Use CDR SDK to parse and verify the SGX quote
      const verificationResult = verifyAttestation(attestationBytes);

      if (!verificationResult) {
         console.error("SGX Attestation failed signature or structural validation.");
         return false;
      }

      const mrenclave = (verificationResult as any).mrenclave || (verificationResult as any).quote?.mrenclave;

      if (mrenclave && typeof mrenclave === 'string') {
          const isCanonical = this.canonicalSeals.includes(mrenclave.toLowerCase());
          if (!isCanonical) {
              console.error(`MRENCLAVE ${mrenclave} not in canonical whitelist.`);
              return false;
          }
      } else {
         console.error("Could not extract MRENCLAVE from attestation.");
         return false;
      }

      console.log("Enclave validation successful. Φ_C compliant.");
      return true;
    } catch (error) {
      console.error("Attestation parsing error:", error);
      return false;
    }
  }
}
