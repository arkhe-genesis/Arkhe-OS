// app/src/main/java/com/arkhe/service/InterstellarSyncService.kt
package com.arkhe.service

import android.app.*
import android.content.Context
import android.content.Intent
import android.os.Build
import android.os.IBinder
import androidx.core.app.NotificationCompat
import com.arkhe.ArkheApplication
import com.arkhe.core.ConsistencyReport
import com.arkhe.core.TemporalMessage
import com.arkhe.core.InterlinkSimulator
import kotlinx.coroutines.*
import java.util.concurrent.ConcurrentHashMap
import android.util.Log

/**
 * Serviço em foreground para sincronização interestelar offline-first.
 *
 * Funcionalidades:
 * - Sincroniza ledger local com peers via Bluetooth/WiFi Direct
 * - Simula enlace laser via InterlinkSimulator (para teste)
 * - Prioriza mensagens por score do Oracle
 * - Mantém operação em background com notificação persistente
 */
import java.util.concurrent.ConcurrentHashMap
import android.util.Log

class InterstellarSyncService : Service() {

    companion object {
        private const val TAG = "InterstellarSync"
        private const val CHANNEL_ID = "arkhe_sync_channel"
        private const val NOTIFICATION_ID = 1001

        private const val SYNC_INTERVAL_SECONDS = 300L
        private const val AGGRESSIVE_SYNC_SECONDS = 60L

        const val ACTION_SYNC_NOW = "com.arkhe.action.SYNC_NOW"
        const val ACTION_ADD_MESSAGE = "com.arkhe.action.ADD_MESSAGE"
        const val EXTRA_MESSAGE = "extra_message"

        /**
         * Inicia o serviço de sincronização.
         */
        fun start(context: Context) {
            val intent = Intent(context, InterstellarSyncService::class.java)
            if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.O) {
                context.startForegroundService(intent)
            } else {
                context.startService(intent)
            }
        }

        /**
         * Adiciona mensagem à fila de sincronização.
         */
        fun queueMessage(context: Context, message: TemporalMessage) {
            val intent = Intent(context, InterstellarSyncService::class.java).apply {
                action = ACTION_ADD_MESSAGE
                putExtra(EXTRA_MESSAGE, message as android.os.Parcelable)
            }
            context.startService(intent)
        }
    }

    private val serviceScope = CoroutineScope(Dispatchers.IO + SupervisorJob())
    private val pendingMessages = ConcurrentHashMap<String, TemporalMessage>()
    }

    private var isSyncing = false
    private var lastSyncTime = 0L

    override fun onCreate() {
        super.onCreate()
        createNotificationChannel()
        startForeground(NOTIFICATION_ID, buildNotification())
        Log.i(TAG, "📡 InterstellarSyncService iniciado")
    }

    override fun onStartCommand(intent: Intent?, flags: Int, startId: Int): Int {
        when (intent?.action) {
            ACTION_SYNC_NOW -> triggerSync(aggressive = true)
            ACTION_ADD_MESSAGE -> {
                intent.getParcelableExtra<TemporalMessage>(EXTRA_MESSAGE)?.let { msg ->
                    pendingMessages[msg.id] = msg
                    Log.d(TAG, "📨 Mensagem adicionada à fila: ${msg.id}")
                }
                Log.d(TAG, "📨 Mensagem adicionada à fila")
            }
        }
        return START_STICKY
    }

    override fun onBind(intent: Intent?): IBinder? = null

    override fun onDestroy() {
        serviceScope.cancel()
        super.onDestroy()
        Log.i(TAG, "🔚 InterstellarSyncService encerrado")
    }

    /**
     * Cria canal de notificação para Android 8.0+.
     */
    private fun createNotificationChannel() {
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.O) {
            val channel = NotificationChannel(
                CHANNEL_ID,
                "ARKHE Sync",
                NotificationManager.IMPORTANCE_LOW
            ).apply {
                description = "Sincronização interestelar em background"
                setShowBadge(false)
            }
            val manager = getSystemService(NotificationManager::class.java)
            manager?.createNotificationChannel(channel)
        }
    }

    /**
     * Constrói notificação persistente para foreground service.
     */
    private fun buildNotification(): Notification {
        val intent = packageManager.getLaunchIntentForPackage(packageName)
        val pendingIntent = PendingIntent.getActivity(
            this, 0, intent,
            PendingIntent.FLAG_IMMUTABLE or PendingIntent.FLAG_UPDATE_CURRENT
        )

        return NotificationCompat.Builder(this, CHANNEL_ID)
            .setContentTitle("ARKHE OS")
            .setContentText("Sincronizando ledger interestelar...")
            .setSmallIcon(android.R.drawable.ic_popup_sync) // Fallback icon
            .setContentIntent(pendingIntent)
            .setPriority(NotificationCompat.PRIORITY_LOW)
            .setOngoing(true)
            .build()
    }

    /**
     * Dispara sincronização imediata.
     */
    fun triggerSync(aggressive: Boolean = false) {
        if (isSyncing) {
            Log.d(TAG, "⏳ Sincronização já em andamento")
            return
        }

        val interval = if (aggressive) AGGRESSIVE_SYNC_SECONDS else SYNC_INTERVAL_SECONDS
        val now = System.currentTimeMillis()

        // Rate limiting
        if (now - lastSyncTime < interval * 1000 && !aggressive) {
            Log.d(TAG, "⏱️ Rate limit: próxima sincronização em ${interval}s")
            return
        }

        lastSyncTime = now
        serviceScope.launch {
            isSyncing = true
            try {
                performSync()
            } catch (e: Exception) {
                Log.e(TAG, "❌ Erro na sincronização", e)
            } finally {
                isSyncing = false
            }
        }
    }

    /**
     * Executa a sincronização principal.
     */
    private suspend fun performSync() {
        Log.i(TAG, "🔄 Iniciando sincronização interestelar")

        val app = applicationContext as ArkheApplication
        val oracle = app.getOracle()
        val hashChain = app.getHashChain()
        // Mock InterlinkSimulator for compilation
        val interlink = InterlinkSimulator(applicationContext)

        // 1. Processar mensagens pendentes
        val messagesToSync = pendingMessages.values.toList()
        for (msg in messagesToSync) {
            val report = oracle.evaluate(msg)

            if (report.consistent) {
                // Mensagem válida: adicionar ao ledger local
                hashChain.appendMessage(msg, report)
                pendingMessages.remove(msg.id)
                Log.d(TAG, "✅ Mensagem ${msg.id} sincronizada (score: ${report.score})")
            } else {
                Log.w(TAG, "⚠️ Mensagem ${msg.id} rejeitada")
                // Manter na fila para retry ou descartar baseado em política
            }
        }

        // 2. Buscar peers próximos (simulado via InterlinkSimulator)
        val peers = interlink.discoverNearbyPeers()
        Log.d(TAG, "🔍 Peers descobertos: ${peers.size}")

        for (peer in peers) {
            try {
                // 3. Estabelecer conexão simulada
                val connection = interlink.connect(peer)

                // 4. Trocar hashes de ledger para detectar divergências
                val localHead = hashChain.getLatestHash()
                val remoteHead = connection.getRemoteLedgerHead()

                if (localHead != remoteHead) {
                    Log.d(TAG, "🔗 Ledger divergente com ${peer.id}: sincronizando...")

                    // 5. Sincronizar blocos faltantes
                    val missingBlocks = connection.fetchMissingBlocks(localHead)
                    for (block in missingBlocks) {
                        val report = oracle.evaluate(block.message)
                        if (report.consistent) {
                            hashChain.appendBlock(block)
                        }
                    }
                }

                connection.close()
            } catch (e: Exception) {
                Log.w(TAG, "⚠️ Falha ao sincronizar com peer ${peer.id}", e)
            }
        }

        // 6. Atualizar notificação
        updateNotification(messagesToSync.size, peers.size)

        Log.i(TAG, "✅ Sincronização concluída")
    }

    /**
     * Atualiza notificação com progresso.
     */
    private fun updateNotification(messagesSynced: Int, peersFound: Int) {
        val notification = NotificationCompat.Builder(this, CHANNEL_ID)
            .setContentTitle("ARKHE OS")
            .setContentText("$messagesSynced mensagens • $peersFound peers")
            .setSmallIcon(android.R.drawable.ic_popup_sync)
            .setPriority(NotificationCompat.PRIORITY_LOW)
            .setOngoing(true)
            .build()

        val manager = getSystemService(NotificationManager::class.java)
        manager?.notify(NOTIFICATION_ID, notification)
    }
}
        isSyncing = true
        try {
            performSync()
        } catch (e: Exception) {
            Log.e(TAG, "❌ Erro na sincronização", e)
        } finally {
            isSyncing = false
        }
    }

    private fun performSync() {
        Log.i(TAG, "🔄 Iniciando sincronização interestelar")

        val app = applicationContext as ArkheApplication
        // val oracle = app.getOracle()
        // val hashChain = app.getHashChain()
        // val interlink = InterlinkSimulator(applicationContext)

        Log.i(TAG, "✅ Sincronização concluída")
    }
}
