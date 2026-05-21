package com.arkhe.citizen

import android.content.Intent
import android.os.Bundle
import io.flutter.embedding.android.FlutterActivity
import io.flutter.embedding.engine.FlutterEngine
import com.arkhe.citizen.plugin.esim.EsimManagerPlugin
import com.arkhe.citizen.detector.nexmon.NexmonFlutterPlugin

/**
 * ARKHE OS — Substrato 408/409
 * MainActivity com registro de plugins nativos
 *
 * Arquiteto: Rafael Oliveira (ORCID: 0009-0005-2697-4668)
 */

class MainActivity : FlutterActivity() {

    private var esimPlugin: EsimManagerPlugin? = null

    override fun configureFlutterEngine(flutterEngine: FlutterEngine) {
        super.configureFlutterEngine(flutterEngine)

        // Registrar plugin eSIM (408)
        esimPlugin = EsimManagerPlugin()
        esimPlugin?.let { plugin ->
            EsimManagerPlugin.registerWithEngine(flutterEngine, this)
            plugin.setActivity(this)
        }

        // Registrar plugin CSI (409)
        NexmonFlutterPlugin.registerWith(flutterEngine, this)
    }

    override fun onActivityResult(requestCode: Int, resultCode: Int, data: Intent?) {
        super.onActivityResult(requestCode, resultCode, data)

        // Delegar resultado para plugins
        if (esimPlugin?.onActivityResult(requestCode, resultCode, data) == true) {
            return
        }
    }

    override fun onDestroy() {
        esimPlugin?.setActivity(null)
        super.onDestroy()
    }
}
