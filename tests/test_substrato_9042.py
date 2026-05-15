#!/usr/bin/env python3
"""Testes para o Substrato 9042 — Coherent Broadcast Mesh."""

import pytest
import asyncio
from unittest.mock import MagicMock
from pyspark.sql import SparkSession

from arkhe_spark import SparkARKHEContext
from arkhe_twitch.mesh_orchestrator import CoherentBroadcastMesh
from arkhe_twitch.twitch_connector import TwitchConfig
from arkhe_twitch.youtube_connector import YouTubeConfig
from arkhe_twitch.tiktok_connector import TikTokConfig

@pytest.fixture(scope="module")
def spark_session():
    """Cria uma SparkSession local para os testes."""
    spark = SparkSession.builder \
        .appName("TestArkheTwitchMesh") \
        .master("local[2]") \
        .getOrCreate()
    yield spark
    spark.stop()

@pytest.fixture
def spark_context(spark_session):
    return SparkARKHEContext(spark_session)

@pytest.mark.asyncio
async def test_add_twitch_stream():
    mesh = CoherentBroadcastMesh()
    config = TwitchConfig("client_id", "secret", "broadcaster_id")
    stream = await mesh.add_stream("twitch_test", "twitch", config)

    assert stream is not None
    assert stream.platform == "twitch"
    assert "twitch_test" in mesh.streams

@pytest.mark.asyncio
async def test_add_youtube_stream():
    mesh = CoherentBroadcastMesh()
    config = YouTubeConfig("api_key", "channel_id")
    stream = await mesh.add_stream("youtube_test", "youtube", config)

    assert stream is not None
    assert stream.platform == "youtube"
    assert "youtube_test" in mesh.streams

@pytest.mark.asyncio
async def test_add_tiktok_stream():
    mesh = CoherentBroadcastMesh()
    config = TikTokConfig("api_key", "user_id")
    stream = await mesh.add_stream("tiktok_test", "tiktok", config)

    assert stream is not None
    assert stream.platform == "tiktok"
    assert "tiktok_test" in mesh.streams

@pytest.mark.asyncio
async def test_spark_processor(spark_context):
    mesh = CoherentBroadcastMesh(spark_context=spark_context)
    config = TwitchConfig("client_id", "secret", "broadcaster_id")
    await mesh.add_stream("spark_twitch", "twitch", config)

    # Simula um evento que será enviado ao buffer
    mesh._on_hype_train("spark_twitch", {"level": 3})

    # O buffer deve ter 1 evento
    assert len(mesh._event_buffer) == 1

    # Simula processamento Spark
    batch = mesh._event_buffer
    mesh._event_buffer = []

    results = mesh.spark_processor.process_stream_events(batch)

    # O processador deve retornar 1 resultado com o impacto Φ_C simulado
    assert len(results) == 1
    assert "processing_result" in results[0]
    assert "phi_c_impact" in results[0]["processing_result"]
    assert results[0]["processing_result"]["phi_c_impact"] == 0.001

@pytest.mark.asyncio
async def test_mesh_status():
    mesh = CoherentBroadcastMesh()
    config = TwitchConfig("client_id", "secret", "broadcaster_id")
    await mesh.add_stream("twitch_status", "twitch", config)

    status = mesh.get_mesh_status()
    assert status["total_streams"] == 1
    assert status["active_streams"] == 0 # Pois o heartbeat não rodou
    assert status["mesh_phi_c"] == 0.0
    assert "twitch_status" in status["stream_details"]
