import os
import asyncio
import json
import logging
from datetime import datetime, timezone

# Dependências de Integração
try:
    from telegram import Bot
except ImportError:
    Bot = None

try:
    import aiohttp
except ImportError:
    aiohttp = None

try:
    from google import genai
except ImportError:
    genai = None

logger = logging.getLogger("ArkheSentinel")
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class ArkheSentinel:
    """
    Agente de Inteligência Autônomo da Arkhe(n).
    Inspirado no Crucix: Monitora, analisa via LLM e alerta via Telegram/Discord.
    """
    def __init__(self):
        self.tg_token = os.getenv("TELEGRAM_BOT_TOKEN")
        self.tg_chat_id = os.getenv("TELEGRAM_CHAT_ID")
        self.discord_webhook = os.getenv("DISCORD_WEBHOOK_URL")
        self.gemini_api_key = os.getenv("GEMINI_API_KEY")

        self.ai_client = None
        if self.gemini_api_key and genai:
            self.ai_client = genai.Client(api_key=self.gemini_api_key)
            logger.info("🧠 Camada LLM Autônoma (Gemini) inicializada.")
        else:
            logger.warning("⚠️ GEMINI_API_KEY não encontrada. Análise LLM desativada.")

    async def broadcast_alert(self, title: str, message: str, level: str = "INFO"):
        """Envia alertas em tempo real para os operadores da rede."""
        full_message = f"[{level}] 🜏 **{title}**\n\n{message}\n\n*Timestamp: {datetime.now(timezone.utc).isoformat()}Z*"
        logger.info(f"Broadcasting: {title}")

        # Telegram Alert
        if self.tg_token and self.tg_chat_id and Bot:
            try:
                bot = Bot(token=self.tg_token)
                await bot.send_message(chat_id=self.tg_chat_id, text=full_message, parse_mode='Markdown')
            except Exception as e:
                logger.error(f"Falha no alerta Telegram: {e}")

        # Discord Alert
        if self.discord_webhook and aiohttp:
            try:
                async with aiohttp.ClientSession() as session:
                    payload = {
                        "username": "Arkhe Sentinel",
                        "avatar_url": "https://arkhe.network/icon.png", # Placeholder
                        "content": full_message
                    }
                    await session.post(self.discord_webhook, json=payload)
            except Exception as e:
                logger.error(f"Falha no alerta Discord: {e}")

    async def analyze_network_health(self, recent_txs: list, zk_proofs: list, phase_data: dict):
        """Usa a camada LLM para gerar insights sobre o fluxo zkERC e saúde da rede."""
        if not self.ai_client:
            return "Análise LLM indisponível."

        prompt = f"""
        Você é o Arkhe(n) Sentinel, um agente de inteligência autônomo monitorando uma rede blockchain baseada em Provas de Conhecimento Zero (STARKs) e Fases Cosmológicas.
        Analise os dados recentes da rede e forneça um relatório de saúde conciso (máximo 3 bullet points).
        Identifique anomalias de consenso, flutuações no tempo de geração das provas ZK ou mudanças abruptas de fase.

        Dados da Rede:
        - Transações zkERC Recentes: {json.dumps(recent_txs)}
        - Métricas de Provas ZK: {json.dumps(zk_proofs)}
        - Estado da Fase Atual: {json.dumps(phase_data)}
        """

        try:
            logger.info("🧠 Solicitando análise de rede ao LLM...")
            response = self.ai_client.models.generate_content(
                model='gemini-3.1-pro-preview',
                contents=prompt,
            )
            insight = response.text

            # Transmite o insight gerado pela IA para os canais
            await self.broadcast_alert("Insight Autônomo da Rede", insight, level="INSIGHT")
            return insight
        except Exception as e:
            logger.error(f"Falha na análise LLM: {e}")
            return str(e)

    async def watch_loop(self):
        """Loop principal de observação (Crucix Watcher)."""
        logger.info("👁️ Sentinela Arkhe(n) iniciou a vigília.")
        await self.broadcast_alert("Sentinela Online", "O Oráculo iniciou a vigília da rede Arkhe(n).", "SYSTEM")
        
        while True:
            try:
                # Aqui integraríamos com o cliente RPC/gRPC do Arkhe Validator
                # Simulando coleta de dados da rede:
                mock_txs = [{"tx_id": "0x123", "type": "zkERC_transfer", "status": "verified"}]
                mock_zk = [{"proof_time_ms": 450, "verifier_status": "ok"}]
                mock_phase = {"current": "Solar", "coherence": 0.98}

                # Executa a análise a cada hora ou quando uma anomalia for detectada
                await self.analyze_network_health(mock_txs, mock_zk, mock_phase)
                
            except Exception as e:
                logger.error(f"Erro no loop de vigília: {e}")
            
            # Aguarda 1 hora antes da próxima análise profunda
            await asyncio.sleep(3600)

if __name__ == "__main__":
    sentinel = ArkheSentinel()
    asyncio.run(sentinel.watch_loop())
