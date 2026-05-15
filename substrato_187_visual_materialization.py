#!/usr/bin/env python3
"""
Arkhe OS - Substrato 187: Visual Materialization
This script runs the visual materialization pipeline integrating Pillow, OpenCV,
Eikon generation, ASCII report cover automation, debug endpoints, and federation.
"""

import asyncio
import cv2
import numpy as np
from PIL import Image
import os

from risomorphism.engine.real_image_processor import RealImageProcessor, ImageProcessingConfig
from risomorphism.video.eikon_generator import RealEikonGenerator, EikonConfig
from transparency.ascii_report_automation import ASCIIReportAutomation, HSMConfig
from api.debug_braille_endpoint import app
from broadcast.eikon_overlay_integration import EikonOverlayIntegrator, EikonOverlayConfig
from security.visual_pqc_signature import VisualPQCSignature
from federation.visual_federation_protocol import VisualFederationProtocol, FederationConfig, VisualAssetType

async def run_demo():
    print("==========================================================")
    print("ARKHE Ω‑TEMP v∞.Ω — SUBSTRATO 187: VISUAL MATERIALIZATION")
    print("==========================================================")

    # Setup test directories
    os.makedirs("/tmp/arkhe_demo", exist_ok=True)
    os.makedirs("output/eikon", exist_ok=True)
    os.makedirs("output/reports", exist_ok=True)

    # 1. RealImageProcessor
    print("\n[1] Processando imagem com Pillow + OpenCV...")
    img = Image.fromarray(np.random.randint(0, 255, (200, 200), dtype=np.uint8))
    test_img_path = "/tmp/arkhe_demo/test_image.png"
    img.save(test_img_path)

    processor = RealImageProcessor(ImageProcessingConfig())
    normalized = processor.load_and_preprocess(test_img_path, (50, 50))
    ascii_art = processor.map_to_glyphs(normalized, "stroke-clarity")
    metrics = processor.calculate_quality_metrics(ascii_art, normalized)
    print(f"✅ Processamento concluído. Quality Verdict: {metrics['verdict']}")

    # 2. EikonGenerator
    print("\n[2] Gerando Eikon de vídeo...")
    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    test_video_path = "/tmp/arkhe_demo/test_video.mp4"
    out = cv2.VideoWriter(test_video_path, fourcc, 24.0, (100, 100))
    for _ in range(24):
        frame = np.random.randint(0, 255, (100, 100, 3), dtype=np.uint8)
        out.write(frame)
    out.release()

    eikon_config = EikonConfig(test_video_path, "output/eikon/demo_eikon.html")
    eikon_gen = RealEikonGenerator(eikon_config)
    eikon_result = await eikon_gen.generate_eikon()
    print(f"✅ Eikon gerado. Frames interpolados: {eikon_result['frames_interpolated']}")

    # 3. ASCII Report Automation
    print("\n[3] Gerando capa ASCII para relatório...")
    hsm_config = HSMConfig()
    report_auto = ASCIIReportAutomation("http://transparency.arkhe.internal", hsm_config)
    report_result = await report_auto.generate_daily_cover()
    print(f"✅ Capa gerada e publicada em: {report_result['public_url']}")

    # 4. Visual PQC Signature
    print("\n[4] Gerando assinatura visual PQC...")
    pqc_sig = VisualPQCSignature()
    sig_result = await pqc_sig.generate_visual_signature(
        "a1b2c3d4e5f6a7b8c9d0e1f2a3b4c5d6e7f8a9b0c1d2e3f4a5b6c7d8e9f0",
        {"algorithm": "Dilithium-3", "key_id": "root-key-01", "timestamp": 1234567890}
    )
    print("✅ Assinatura visual gerada:")
    print(sig_result["visual_signature"])

    # 5. Visual Federation Protocol
    print("\n[5] Publicando na Federação Cross-Org...")
    fed_config = FederationConfig("arkhe-core", {"arkhe-core", "partner-bank"})
    federation = VisualFederationProtocol(fed_config)
    fed_asset = await federation.publish_asset(
        VisualAssetType.ASCII_RENDER,
        ascii_art,
        {"description": "Test render", "phi_c": 0.999}
    )
    print(f"✅ Ativo federado publicado. Asset ID: {fed_asset.asset_id}")

    print("\n==========================================================")
    print("✅ MATERIALIZAÇÃO VISUAL (SUBSTRATO 187) CONCLUÍDA")
    print("==========================================================")

if __name__ == "__main__":
    asyncio.run(run_demo())
