import { ethers } from 'ethers'
import Safe, { SafeFactory, SafeAccountConfig } from '@safe-global/protocol-kit'
import { EthersAdapter } from '@safe-global/protocol-kit'
import SafeApiKit from '@safe-global/api-kit'

export interface SafeConfig {
  ownerKey: string
  rpcUrl: string
  txServiceUrl: string
}

/**
 * SafeAccountManager manages Gnosis Safe multi-sig accounts for Arkhe agents.
 * It handles JanusLock signatures and economic transactions.
 */
export class SafeAccountManager {
  private provider: ethers.JsonRpcProvider
  private signer: ethers.Wallet
  private safeApiKit: SafeApiKit

  constructor(config: SafeConfig) {
    this.provider = new ethers.JsonRpcProvider(config.rpcUrl)
    this.signer = new ethers.Wallet(config.ownerKey, this.provider)
    this.safeApiKit = new SafeApiKit({
      chainId: 11155111n, // Sepolia
      txServiceUrl: config.txServiceUrl
    })
  }

  /**
   * Deploys a new Safe with the specified owners and threshold.
   */
  async deploySafe(owners: string[], threshold: number): Promise<string> {
    const safeFactory = await SafeFactory.create({
      ethAdapter: this._getEthAdapter()
    })
    const safeAccountConfig: SafeAccountConfig = {
      owners,
      threshold
    }
    const safe = await safeFactory.deploySafe({ safeAccountConfig })
    return await safe.getAddress()
  }

  /**
   * Signs a JanusLock coherence proof transaction.
   */
  async signCoherenceProof(safeAddress: string, lambda: number, block: number): Promise<string> {
    const safe = await Safe.init({
      ethAdapter: this._getEthAdapter(),
      safeAddress
    })

    // Data encoding for ARKHE_COHERENCE_OK (mock call)
    const data = ethers.id(`ARKHE_COHERENCE_OK(${lambda},${block})`)

    const safeTransaction = await safe.createTransaction({
      transactions: [{
        to: safeAddress,
        value: '0',
        data
      }]
    })

    const safeTxHash = await safe.getTransactionHash(safeTransaction)
    const signature = await safe.signHash(safeTxHash)

    return signature.data
  }

  private _getEthAdapter() {
    return new EthersAdapter({
      ethers,
      signerOrProvider: this.signer
    })
  }
}
