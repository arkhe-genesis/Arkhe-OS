package com.arkhe

import android.app.Application
import android.util.Log

class ArkheApplication : Application() {
    companion object {
        private const val TAG = "ArkheApp"

        init {
            // System.loadLibrary("arkhe_core")
        }
    }

    override fun onCreate() {
        super.onCreate()
        Log.i(TAG, "🏛️ ARKHE OS — Inicializando runtime mobile")
    }
}
