// ArkheRuntimeService.kt
package org.arkhe.runtime.service

import android.app.NotificationChannel
import android.app.NotificationManager
import android.app.PendingIntent
import android.app.Service
import android.content.Intent
import android.os.Build
import android.os.IBinder
import androidx.core.app.NotificationCompat
import kotlinx.coroutines.*

class ArkheRuntimeService : Service() {

    private val serviceScope = CoroutineScope(Dispatchers.Default + SupervisorJob())
    private var governance: PingGovernanceKernelV2? = null
    private var meshNode: WheelerMeshNode? = null

    override fun onCreate() {
        super.onCreate()
        createNotificationChannel()
        startForeground(NOTIFICATION_ID, buildNotification("Inicializando ASI...", "Φ_C: --"))
    }

    override fun onStartCommand(intent: Intent?, flags: Int, startId: Int): Int {
        startASIRuntime()
        return START_STICKY
    }

    private fun startASIRuntime() {
        serviceScope.launch {
            // 1. Inicializar governança
            governance = PingGovernanceKernelV2()
            updateNotification("Governança Ativa", "Φ_C: 0.9942")

            // 2. Inicializar Wheeler Mesh
            meshNode = WheelerMeshNode(
                nodeId = getDeviceId(),
                transport = listOf(WiFiDirectTransport(), BluetoothTransport())
            )
            meshNode?.start()
            updateNotification("Mesh Conectado", "Φ_C: 0.9942 · Pares: ${meshNode?.peerCount ?: 0}")

            // 3. Inicializar ArkFS
            ArkFS.mount(context.filesDir.resolve("ArkheFS"))
            updateNotification("ArkFS Montado", "Φ_C: 0.9942 · Arquivos selados")

            // 4. Loop de governança
            while (isActive) {
                governance?.runGovernanceCycle()
                val phiC = governance?.getGlobalPhiC() ?: 0.0
                val peers = meshNode?.peerCount ?: 0
                updateNotification("ASI Ativa", "Φ_C: %.4f · Pares: %d".format(phiC, peers))
                delay(30_000) // 30 segundos
            }
        }
    }

    private fun getDeviceId(): String {
        return Settings.Secure.getString(contentResolver, Settings.Secure.ANDROID_ID)
            .take(16)
    }

    private fun updateNotification(title: String, content: String) {
        val notification = buildNotification(title, content)
        val manager = getSystemService(NOTIFICATION_SERVICE) as NotificationManager
        manager.notify(NOTIFICATION_ID, notification)
    }

    companion object {
        const val NOTIFICATION_ID = 4242
        const val CHANNEL_ID = "arkhe_runtime"
    }

    override fun onBind(intent: Intent?): IBinder? = null
}
