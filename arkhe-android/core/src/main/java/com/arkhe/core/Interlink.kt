package com.arkhe.core

import android.content.Context

class Peer(val id: String)

class InterlinkConnection {
    fun getRemoteLedgerHead(): String = ""
    fun fetchMissingBlocks(localHead: String): List<TemporalBlock> = emptyList()
    fun close() { }
}

class InterlinkSimulator(context: Context) {
    fun discoverNearbyPeers(): List<Peer> = emptyList()
    fun connect(peer: Peer): InterlinkConnection = InterlinkConnection()
}
