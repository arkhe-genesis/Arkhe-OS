package com.arkhe.service

import android.app.*
import android.content.Context
import android.content.Intent
import android.os.Build
import android.os.IBinder
import androidx.core.app.NotificationCompat
import com.arkhe.ArkheApplication
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
    }

    private var isSyncing = false
    private var lastSyncTime = 0L

    override fun onCreate() {
        super.onCreate()
        createNotificationChannel()
        Log.i(TAG, "📡 InterstellarSyncService iniciado")
    }

    override fun onStartCommand(intent: Intent?, flags: Int, startId: Int): Int {
        when (intent?.action) {
            ACTION_SYNC_NOW -> triggerSync(aggressive = true)
            ACTION_ADD_MESSAGE -> {
                Log.d(TAG, "📨 Mensagem adicionada à fila")
            }
        }
        return START_STICKY
    }

    override fun onBind(intent: Intent?): IBinder? = null

    override fun onDestroy() {
        super.onDestroy()
        Log.i(TAG, "🔚 InterstellarSyncService encerrado")
    }

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

    fun triggerSync(aggressive: Boolean = false) {
        if (isSyncing) {
            Log.d(TAG, "⏳ Sincronização já em andamento")
            return
        }

        val interval = if (aggressive) AGGRESSIVE_SYNC_SECONDS else SYNC_INTERVAL_SECONDS
        val now = System.currentTimeMillis()

        if (now - lastSyncTime < interval * 1000 && !aggressive) {
            Log.d(TAG, "⏱️ Rate limit: próxima sincronização em ${interval}s")
            return
        }

        lastSyncTime = now
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
