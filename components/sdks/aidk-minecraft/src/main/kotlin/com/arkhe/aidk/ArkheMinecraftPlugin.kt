package com.arkhe.aidk

import com.auth0.jwt.JWT
import com.auth0.jwt.algorithms.Algorithm
import com.google.gson.Gson
import com.google.gson.annotations.SerializedName
import okhttp3.MediaType.Companion.toMediaType
import okhttp3.OkHttpClient
import okhttp3.Request
import okhttp3.RequestBody.Companion.toRequestBody
import org.bukkit.*
import org.bukkit.event.EventHandler
import org.bukkit.event.Listener
import org.bukkit.event.block.Action
import org.bukkit.event.player.PlayerInteractEvent
import org.bukkit.inventory.ItemStack
import org.bukkit.plugin.java.JavaPlugin
import java.util.*
import java.util.concurrent.TimeUnit

data class GameEvent(
    @SerializedName("game_id") val gameId: String,
    @SerializedName("event_id") val eventId: UUID = UUID.randomUUID(),
    @SerializedName("player_id") val playerId: String,
    val action: String,
    val target: TargetData,
    val metadata: Map<String, Any>? = null
)

data class TargetData(
    val type: String,
    val data: Map<String, Any>
)

data class ArkheResponse(
    val result: String,
    val severity: String,
    @SerializedName("visual_feedback") val feedback: VisualFeedback?,
    val reward: Reward?,
    @SerializedName("audit_ref") val auditRef: String
)

data class VisualFeedback(
    val color: String,
    val animation: String,
    @SerializedName("sound_id") val soundId: String
)

data class Reward(
    val currency: String,
    val amount: Int
)

class ArkheMinecraftPlugin : JavaPlugin(), Listener {

    private val httpClient = OkHttpClient.Builder()
        .connectTimeout(10, TimeUnit.SECONDS)
        .readTimeout(30, TimeUnit.SECONDS)
        .build()
    private val gson = Gson()
    private var arkheApiUrl: String = "http://localhost:8000"
    private var jwtSecret: String = "dummy-secret"

    override fun onEnable() {
        saveDefaultConfig()
        arkheApiUrl = config.getString("arkhe.api.url") ?: "http://localhost:8000"
        jwtSecret = config.getString("arkhe.api.jwt_secret") ?: "dummy-secret"

        server.pluginManager.registerEvents(this, this)
        logger.info("Arkhe Integration enabled. Protecting the realm.")
    }

    @EventHandler
    fun onPlayerInteract(event: PlayerInteractEvent) {
        if (event.action != Action.RIGHT_CLICK_BLOCK) return
        val block = event.clickedBlock ?: return

        // Audit material from config (default COMMAND_BLOCK)
        val auditMaterial = Material.valueOf(config.getString("gameplay.audit_block_material") ?: "COMMAND_BLOCK")
        if (block.type != auditMaterial) return

        val player = event.player
        val loc = block.location

        // Anonymize player ID
        val anonymizedId = player.uniqueId.toString()
            .toByteArray()
            .let { java.security.MessageDigest.getInstance("SHA-256").digest(it) }
            .joinToString("") { "%02x".format(it) }
            .take(16)

        val payload = GameEvent(
            gameId = "minecraft-sre",
            playerId = anonymizedId,
            action = "scan",
            target = TargetData(
                type = "coordinate",
                data = mapOf(
                    "x" to loc.blockX,
                    "y" to loc.blockY,
                    "z" to loc.blockZ,
                    "world" to loc.world?.name.toString()
                )
            ),
            metadata = mapOf(
                "game_mode" to player.gameMode.name
            )
        )

        Bukkit.getScheduler().runTaskAsynchronously(this, Runnable {
            try {
                val result = sendToArkhe(payload)
                Bukkit.getScheduler().runTask(this, Runnable {
                    handleResponse(player, loc, result)
                })
            } catch (e: Exception) {
                logger.warning("Failed to send event: ${e.message}")
            }
        })
    }

    private fun sendToArkhe(event: GameEvent): ArkheResponse? {
        val token = JWT.create()
            .withClaim("game_id", event.gameId)
            .withClaim("scope", "gameplay.write")
            .withIssuedAt(Date())
            .withExpiresAt(Date(System.currentTimeMillis() + TimeUnit.HOURS.toMillis(24)))
            .sign(Algorithm.HMAC256(jwtSecret))

        val json = gson.toJson(event)
        val body = json.toRequestBody("application/json".toMediaType())
        val request = Request.Builder()
            .url("$arkheApiUrl/api/v1/gameplay/event")
            .header("Authorization", "Bearer $token")
            .post(body)
            .build()

        return httpClient.newCall(request).execute().use { response ->
            if (!response.isSuccessful) null
            else gson.fromJson(response.body?.string(), ArkheResponse::class.java)
        }
    }

    private fun handleResponse(player: Player, loc: Location, result: ArkheResponse?) {
        when (result?.result) {
            "confirmed" -> {
                val particleType = Particle.valueOf(config.getString("gameplay.success_particle") ?: "PORTAL")
                val soundType = Sound.valueOf(config.getString("gameplay.success_sound") ?: "BLOCK_BEACON_POWER_SELECT")

                player.world.spawnParticle(particleType, loc.toCenterLocation(), 100)
                player.world.playSound(loc, soundType, 1.0f, 2.0f)

                player.sendMessage("§a[Arkhe] Anomalia Confirmada! Recompensa: ${result.reward?.amount} ${result.reward?.currency}")

                if (result.reward?.currency == "EMERALD") {
                    player.inventory.addItem(ItemStack(Material.EMERALD, result.reward.amount))
                }

                loc.block.type = Material.EMERALD_BLOCK
            }
            "false_positive" -> {
                player.sendMessage("§e[Arkhe] Nenhuma anomalia detectada neste quadrante.")
            }
            else -> {
                player.sendMessage("§c[Arkhe] Scanner indisponível.")
            }
        }
    }
}
