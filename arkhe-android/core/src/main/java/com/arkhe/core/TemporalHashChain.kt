package com.arkhe.core

import javax.crypto.SecretKey

class TemporalBlock(val message: TemporalMessage)

class TemporalHashChain(
    val genesisHash: String,
    val encryptionKey: SecretKey,
    val compressionEnabled: Boolean
) {
    fun recordEvent(type: String, payload: Map<String, Any>) { }

    fun appendMessage(msg: TemporalMessage, report: ConsistencyReport) { }

    fun appendBlock(block: TemporalBlock) { }

    fun getLatestHash(): String = ""
}
