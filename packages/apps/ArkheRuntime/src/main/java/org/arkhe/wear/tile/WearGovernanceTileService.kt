// WearGovernanceTileService.kt
package org.arkhe.wear.tile

import android.content.Context
import androidx.wear.protolayout.ModBuilders
import androidx.wear.protolayout.ResourceBuilders
import androidx.wear.tiles.TileProviderService
import androidx.wear.tiles.tooling.TileData

class WearGovernanceTileService : TileProviderService() {
    override fun onTileRequest(requestParams: TileRequestParams): TileData {
        val metrics = ArkheRuntimeClient.getMetrics()

        val layout = ModBuilders.Column.Builder()
            .addContent(
                ModBuilders.Text.Builder()
                    .setText("Φ_C: %.4f".format(metrics.phiC))
                    .setMaxLines(1)
                    .build()
            )
            .addContent(
                ModBuilders.Text.Builder()
                    .setText("π: %.4f".format(metrics.pi))
                    .setMaxLines(1)
                    .build()
            )
            .build()

        return TileData.Builder()
            .setResources(ResourceBuilders.Resources.Builder().build())
            .setTile(ModBuilders.Tile.Builder()
                .setFreshnessIntervalMillis(30_000)
                .setTileLayout(layout)
                .build())
            .build()
    }
}
