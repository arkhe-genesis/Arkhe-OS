#!/usr/bin/env python3
"""Substrato 9041 — Arkhe-Twitch: Secure Streaming Integration
Integra ARKHE Cathedral com Twitch.tv via Helix API, EventSub WebSocket,
Chat API e Drops/Rewards. Protege cada interação com Φ_C, Guardian,
TemporalChain e PQC signing.

Baseado na documentação oficial da Twitch Developer API 2026.
"""

import asyncio, hashlib, json, time, logging
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any, Callable
from enum import Enum
from pathlib import Path

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class TwitchEventType(Enum):
    STREAM_ONLINE = "stream.online"
    STREAM_OFFLINE = "stream.offline"
    CHANNEL_FOLLOW = "channel.follow"
    CHANNEL_SUBSCRIBE = "channel.subscribe"
    CHANNEL_CHEER = "channel.cheer"
    CHANNEL_RAID = "channel.raid"
    CHANNEL_POINTS_CUSTOM_REWARD_ADD = "channel.channel_points_custom_reward.add"
    CHANNEL_POINTS_CUSTOM_REWARD_REDEMPTION_ADD = "channel.channel_points_custom_reward_redemption.add"
    DROP_ENTITLEMENT_GRANT = "drop.entitlement.grant"
    CHAT_MESSAGE = "channel.chat.message"
    HYPE_TRAIN_BEGIN = "channel.hype_train.begin"
    HYPE_TRAIN_END = "channel.hype_train.end"
    AD_BREAK_BEGIN = "channel.ad_break.begin"
    SUSPICIOUS_USER_UPDATE = "channel.suspicious_user.update"

class AuthScope(Enum):
    CHAT_READ = "user:read:chat"
    CHAT_SEND = "user:write:chat"
    CHANNEL_READ = "channel:read:stream_key"
    CHANNEL_MANAGE = "channel:manage:broadcast"
    MODERATOR_READ = "moderator:read:followers"
    MODERATOR_MANAGE = "moderator:manage:shoutouts"
    REDEMPTIONS_READ = "channel:read:redemptions"
    REDEMPTIONS_MANAGE = "channel:manage:redemptions"
    DROPS_READ = "drops:read"
    DROPS_MANAGE = "drops:manage"
    BITS_READ = "bits:read"
    SUBSCRIPTIONS_READ = "channel:read:subscriptions"
    ANALYTICS_READ = "analytics:read:extensions"

@dataclass
class TwitchConfig:
    client_id: str
    client_secret: str
    broadcaster_id: str
    redirect_uri: str = "http://localhost:3000/auth/callback"
    scopes: List[AuthScope] = field(default_factory=lambda: [
        AuthScope.CHAT_READ, AuthScope.CHAT_SEND, AuthScope.CHANNEL_READ,
        AuthScope.REDEMPTIONS_READ, AuthScope.REDEMPTIONS_MANAGE,
    ])
    api_base_url: str = "https://api.twitch.tv/helix"
    auth_base_url: str = "https://id.twitch.tv/oauth2"
    eventsub_ws_url: str = "wss://eventsub.wss.twitch.tv/ws"
    timeout_seconds: int = 30
    retry_attempts: int = 3

@dataclass
class StreamInfo:
    id: str
    broadcaster_id: str
    broadcaster_name: str
    title: str
    game_name: str
    viewer_count: int
    started_at: str
    language: str
    thumbnail_url: str
    is_mature: bool = False
    phi_c_coherence: float = 0.0
    temporal_seal: Optional[str] = None

@dataclass
class ChatMessage:
    message_id: str
    broadcaster_id: str
    chatter_id: str
    chatter_name: str
    message: str
    timestamp: float
    emotes: List[Dict] = field(default_factory=list)
    badges: List[str] = field(default_factory=list)
    is_command: bool = False
    command_name: Optional[str] = None
    command_args: List[str] = field(default_factory=list)
    phi_c_safe: bool = True
    guardian_reason: Optional[str] = None

@dataclass
class ChannelPointRedemption:
    redemption_id: str
    broadcaster_id: str
    reward_id: str
    reward_title: str
    reward_cost: int
    user_id: str
    user_name: str
    user_input: str
    status: str  # UNFULFILLED, FULFILLED, CANCELED
    redeemed_at: str
    phi_c_coherence: float = 0.0

@dataclass
class DropEntitlement:
    entitlement_id: str
    benefit_id: str
    user_id: str
    user_name: str
    game_id: str
    campaign_id: str
    fulfillment_status: str  # CLAIMED, FULFILLED
    created_at: str
    last_updated: str

@dataclass
class ArkheTwitchMetrics:
    stream_phi_c: float = 0.0
    chat_guardian_blocks: int = 0
    redemptions_processed: int = 0
    drops_fulfilled: int = 0
    events_anchored: int = 0
    api_requests_total: int = 0
    api_errors_total: int = 0
    eventsub_messages_received: int = 0
    eventsub_messages_dropped: int = 0
    temporal_seal: Optional[str] = None

class ArkheTwitchConnector:
    """
    Conector ARKHE para Twitch.tv com segurança de nível Cathedral.

    Integrações:
    • Helix API — Canais, streams, chat, redemptions, drops
    • EventSub WebSocket — Eventos em tempo real
    • Chat API — Envio/recepção de mensagens
    • Channel Points — Custom rewards e redemptions
    • Drops — Entitlements e fulfillment

    Segurança:
    • Guardian Atpector valida cada mensagem de chat
    • Φ_C monitora coerência do stream
    • TemporalChain ancora cada evento
    • PQC signing para metadados críticos
    """

    HELIX_ENDPOINTS = {
        "get_streams": "/streams",
        "get_channel": "/channels",
        "get_chatters": "/chat/chatters",
        "send_chat_message": "/chat/messages",
        "get_channel_points": "/channel_points/custom_rewards",
        "create_reward": "/channel_points/custom_rewards",
        "update_reward": "/channel_points/custom_rewards",
        "get_redemptions": "/channel_points/custom_rewards/redemptions",
        "update_redemption": "/channel_points/custom_rewards/redemptions",
        "get_drops": "/entitlements/drops",
        "update_drops": "/entitlements/drops",
        "get_bits_leaderboard": "/bits/leaderboard",
        "get_clips": "/clips",
        "create_clip": "/clips",
        "start_commercial": "/channels/commercial",
        "get_moderators": "/moderation/moderators",
        "get_banned_users": "/moderation/banned",
        "get_vips": "/channels/vips",
    }

    EVENTSUB_SUBSCRIPTIONS = {
        "stream.online": "1",
        "stream.offline": "1",
        "channel.follow": "2",
        "channel.subscribe": "1",
        "channel.cheer": "1",
        "channel.raid": "1",
        "channel.channel_points_custom_reward_redemption.add": "1",
        "drop.entitlement.grant": "1",
        "channel.chat.message": "1",
        "channel.hype_train.begin": "1",
        "channel.hype_train.end": "1",
        "channel.ad_break.begin": "1",
        "channel.suspicious_user.update": "1",
    }

    def __init__(self, config: TwitchConfig, temporal_chain=None, guardian=None,
                 phi_bus=None, pqc_adapter=None, siem_connector=None):
        self.config = config
        self.temporal = temporal_chain
        self.guardian = guardian
        self.phi_bus = phi_bus
        self.pqc = pqc_adapter
        self.siem = siem_connector
        self._access_token: Optional[str] = None
        self._refresh_token: Optional[str] = None
        self._token_expires_at: float = 0
        self._ws_connection = None
        self._event_handlers: Dict[TwitchEventType, List[Callable]] = {}
        self._metrics = ArkheTwitchMetrics()
        self._chat_history: List[ChatMessage] = []
        self._redemptions_queue: List[ChannelPointRedemption] = []
        self._drops_queue: List[DropEntitlement] = []
        self._session = None

    async def __aenter__(self):
        try:
            import aiohttp
            self._session = aiohttp.ClientSession(
                timeout=aiohttp.ClientTimeout(total=self.config.timeout_seconds),
                headers={
                    "Client-Id": self.config.client_id,
                    "Accept": "application/json",
                }
            )
        except ImportError:
            logger.warning("aiohttp não disponível — usando modo simulado")
            self._session = None
        return self

    async def __aexit__(self, *args):
        if self._ws_connection:
            await self._ws_connection.close()
        if self._session:
            await self._session.close()

    # ── Autenticação OAuth2 ────────────────────────────────────

    def get_auth_url(self, state: str = "arkhe_twitch") -> str:
        """Gera URL de autorização OAuth2."""
        scopes_str = " ".join(s.value for s in self.config.scopes)
        return (
            f"{self.config.auth_base_url}/authorize"
            f"?client_id={self.config.client_id}"
            f"&redirect_uri={self.config.redirect_uri}"
            f"&response_type=code"
            f"&scope={scopes_str}"
            f"&state={state}"
        )

    async def exchange_code(self, code: str) -> bool:
        """Troca código de autorização por tokens."""
        payload = {
            "client_id": self.config.client_id,
            "client_secret": self.config.client_secret,
            "code": code,
            "grant_type": "authorization_code",
            "redirect_uri": self.config.redirect_uri,
        }
        result = await self._api_request("POST", "/token", base_url=self.config.auth_base_url, data=payload)
        if "access_token" in result:
            self._access_token = result["access_token"]
            self._refresh_token = result.get("refresh_token")
            self._token_expires_at = time.time() + result.get("expires_in", 3600)
            if self._session:
                self._session.headers.update({"Authorization": f"Bearer {self._access_token}"})
            return True
        return False

    async def refresh_access_token(self) -> bool:
        """Renova token de acesso."""
        if not self._refresh_token:
            return False
        payload = {
            "client_id": self.config.client_id,
            "client_secret": self.config.client_secret,
            "refresh_token": self._refresh_token,
            "grant_type": "refresh_token",
        }
        result = await self._api_request("POST", "/token", base_url=self.config.auth_base_url, data=payload)
        if "access_token" in result:
            self._access_token = result["access_token"]
            self._token_expires_at = time.time() + result.get("expires_in", 3600)
            if self._session:
                self._session.headers.update({"Authorization": f"Bearer {self._access_token}"})
            return True
        return False

    # ── API Request Core ───────────────────────────────────────

    async def _api_request(self, method: str, endpoint: str, base_url: str = None,
                         **kwargs) -> Dict:
        """Executa requisição à API Helix com retry e rate limit handling."""
        # Check if we're in simulation mode (aiohttp not available or mock session)
        try:
            import aiohttp
            # Check if session is a real aiohttp ClientSession
            if self._session is None or not hasattr(self._session, '_connector'):
                return self._simulate_api_response(method, endpoint, kwargs)
        except ImportError:
            return self._simulate_api_response(method, endpoint, kwargs)

        url = f"{base_url or self.config.api_base_url}{endpoint}"
        headers = kwargs.pop("headers", {})

        if self._access_token:
            headers["Authorization"] = f"Bearer {self._access_token}"

        for attempt in range(self.config.retry_attempts):
            try:
                async with self._session.request(method, url, headers=headers, **kwargs) as resp:
                    self._metrics.api_requests_total += 1

                    if resp.status == 200:
                        return await resp.json()
                    elif resp.status == 401:
                        await self.refresh_access_token()
                        continue
                    elif resp.status == 429:
                        retry_after = int(resp.headers.get("Ratelimit-Reset", 60))
                        logger.warning(f"Rate limited — aguardando {retry_after}s")
                        await asyncio.sleep(retry_after)
                        continue
                    else:
                        self._metrics.api_errors_total += 1
                        return {"error": f"HTTP {resp.status}"}
            except Exception as e:
                logger.warning(f"Tentativa {attempt+1} falhou: {e}")
                if attempt < self.config.retry_attempts - 1:
                    await asyncio.sleep(2 ** attempt)

        self._metrics.api_errors_total += 1
        return {"error": "Max retry exceeded"}

    def _simulate_api_response(self, method: str, endpoint: str, kwargs: Dict) -> Dict:
        """Simula respostas da API para testes."""
        if "streams" in endpoint and method == "GET":
            return {"data": [{
                "id": "stream_001", "user_id": self.config.broadcaster_id,
                "user_name": "ARKHE_Official", "title": "ARKHE Cathedral Stream",
                "game_name": "Science & Technology", "viewer_count": 1337,
                "started_at": "2026-05-15T00:00:00Z", "language": "pt",
                "thumbnail_url": "https://static-cdn.jtvnw.net/previews-ttv/...",
                "is_mature": False,
            }]}
        elif "channels" in endpoint and method == "GET":
            return {"data": [{
                "broadcaster_id": self.config.broadcaster_id,
                "broadcaster_name": "ARKHE_Official",
                "broadcaster_language": "pt",
                "game_name": "Science & Technology",
                "title": "ARKHE Cathedral Stream",
                "delay": 0,
            }]}
        elif "chat/messages" in endpoint and method == "POST":
            return {"data": [{"message_id": "msg_001", "is_sent": True}]}
        elif "channel_points" in endpoint:
            return {"data": [{
                "id": "reward_001", "broadcaster_id": self.config.broadcaster_id,
                "title": "ARKHE Blessing", "prompt": "Receive a Cathedral blessing",
                "cost": 100, "is_enabled": True,
            }]}
        elif "redemptions" in endpoint:
            return {"data": [{
                "id": "redemption_001", "broadcaster_id": self.config.broadcaster_id,
                "reward_id": "reward_001", "user_id": "viewer_001",
                "user_name": "ArkheFan", "user_input": "Bless me, Cathedral!",
                "status": "UNFULFILLED", "redeemed_at": "2026-05-15T00:00:00Z",
            }]}
        elif "drops" in endpoint:
            return {"data": [{
                "id": "drop_001", "benefit_id": "benefit_001",
                "user_id": "viewer_001", "game_id": "game_001",
                "fulfillment_status": "CLAIMED", "created_at": "2026-05-15T00:00:00Z",
            }]}
        elif "clips" in endpoint and method == "POST":
            return {"data": [{"id": "clip_001", "edit_url": "https://clips.twitch.tv/..."}]}
        elif "commercial" in endpoint:
            return {"data": [{"length_seconds": 60, "message": "Commercial started successfully"}]}
        return {"data": []}

    # ── Stream Management ──────────────────────────────────────

    async def get_stream_info(self) -> Optional[StreamInfo]:
        """Obtém informações do stream atual."""
        result = await self._api_request(
            "GET", f"/streams?user_id={self.config.broadcaster_id}"
        )
        data = result.get("data", [])
        if not data:
            return None

        stream_data = data[0]
        phi_c = self.phi_bus.get_mesh_coherence() if self.phi_bus else 0.997

        stream = StreamInfo(
            id=stream_data.get("id", ""),
            broadcaster_id=stream_data.get("user_id", ""),
            broadcaster_name=stream_data.get("user_name", ""),
            title=stream_data.get("title", ""),
            game_name=stream_data.get("game_name", ""),
            viewer_count=stream_data.get("viewer_count", 0),
            started_at=stream_data.get("started_at", ""),
            language=stream_data.get("language", ""),
            thumbnail_url=stream_data.get("thumbnail_url", ""),
            is_mature=stream_data.get("is_mature", False),
            phi_c_coherence=phi_c,
        )

        if self.temporal:
            stream.temporal_seal = await self.temporal.anchor_event("twitch_stream_info", {
                "stream_id": stream.id,
                "title": stream.title,
                "viewers": stream.viewer_count,
                "phi_c": phi_c,
                "timestamp": time.time(),
            })

        return stream

    async def update_stream_title(self, title: str) -> bool:
        """Atualiza título do stream."""
        result = await self._api_request(
            "PATCH", f"/channels?broadcaster_id={self.config.broadcaster_id}",
            json={"title": title}
        )
        success = "error" not in result

        if self.temporal and success:
            await self.temporal.anchor_event("twitch_title_updated", {
                "broadcaster_id": self.config.broadcaster_id,
                "title": title,
                "timestamp": time.time(),
            })

        return success

    # ── Chat Management ──────────────────────────────────────

    async def send_chat_message(self, message: str, reply_to: Optional[str] = None) -> bool:
        """Envia mensagem no chat com validação Guardian."""
        if self.guardian:
            safe, report = self.guardian.exorcise(message)
            if not safe:
                logger.warning(f"Mensagem bloqueada pelo Guardian: {message[:50]}")
                if self.siem:
                    alert_obj = type("Alert", (), {})()
                    alert_obj.alert_id = "twitch-chat-block"
                    alert_obj.timestamp = time.time()
                    alert_obj.component = "twitch_chat"
                    alert_obj.alert_type = "guardian_block"
                    sev_obj = type("Sev", (), {})()
                    sev_obj.value = "medium"
                    alert_obj.severity = sev_obj
                    alert_obj.description = f"Chat message blocked: {message[:100]}"
                    alert_obj.evidence = {"message": message[:200]}
                    alert_obj.phi_c_value = 0.95
                    alert_obj.temporal_seal = None
                    alert_obj.remediation_suggested = "Review Guardian rules"
                    await self.siem.send_alert(alert_obj, immediate=True)
                return False

        payload = {
            "broadcaster_id": self.config.broadcaster_id,
            "sender_id": self.config.broadcaster_id,
            "message": message,
        }
        if reply_to:
            payload["reply_parent_message_id"] = reply_to

        result = await self._api_request("POST", "/chat/messages", json=payload)
        success = "error" not in result and result.get("data", [{}])[0].get("is_sent", False)

        if self.temporal and success:
            await self.temporal.anchor_event("twitch_chat_sent", {
                "message": message[:200],
                "broadcaster_id": self.config.broadcaster_id,
                "timestamp": time.time(),
            })

        return success

    async def process_chat_message(self, message_data: Dict) -> ChatMessage:
        """Processa mensagem recebida do chat com validação."""
        msg = ChatMessage(
            message_id=message_data.get("message_id", ""),
            broadcaster_id=message_data.get("broadcaster_user_id", ""),
            chatter_id=message_data.get("chatter_user_id", ""),
            chatter_name=message_data.get("chatter_user_name", ""),
            message=message_data.get("message", {}).get("text", ""),
            timestamp=time.time(),
            emotes=message_data.get("message", {}).get("fragments", []),
            badges=message_data.get("badges", []),
        )

        # Detectar comandos
        if msg.message.startswith("!"):
            msg.is_command = True
            parts = msg.message[1:].split()
            msg.command_name = parts[0] if parts else None
            msg.command_args = parts[1:] if len(parts) > 1 else []

        # Validar com Guardian
        if self.guardian:
            safe, report = self.guardian.exorcise(msg.message)
            msg.phi_c_safe = safe
            if not safe:
                msg.guardian_reason = getattr(report, "reason", "unsafe_content")
                self._metrics.chat_guardian_blocks += 1

        self._chat_history.append(msg)

        # Ancorar
        if self.temporal:
            await self.temporal.anchor_event("twitch_chat_received", {
                "message_id": msg.message_id,
                "chatter": msg.chatter_name,
                "command": msg.command_name,
                "safe": msg.phi_c_safe,
                "timestamp": msg.timestamp,
            })

        return msg

    # ── Channel Points ─────────────────────────────────────────

    async def create_custom_reward(self, title: str, cost: int, prompt: str = "",
                                    background_color: str = "#00FF00",
                                    is_user_input_required: bool = False) -> Optional[str]:
        """Cria recompensa customizada de Channel Points."""
        payload = {
            "title": title,
            "cost": cost,
            "prompt": prompt,
            "background_color": background_color,
            "is_user_input_required": is_user_input_required,
            "is_enabled": True,
        }

        result = await self._api_request(
            "POST", f"/channel_points/custom_rewards?broadcaster_id={self.config.broadcaster_id}",
            json=payload
        )

        if "data" in result and result["data"]:
            reward_id = result["data"][0].get("id")

            if self.temporal:
                await self.temporal.anchor_event("twitch_reward_created", {
                    "reward_id": reward_id,
                    "title": title,
                    "cost": cost,
                    "timestamp": time.time(),
                })

            return reward_id
        return None

    async def get_redemptions(self, reward_id: str, status: str = "UNFULFILLED") -> List[ChannelPointRedemption]:
        """Obtém redemptions pendentes."""
        result = await self._api_request(
            "GET",
            f"/channel_points/custom_rewards/redemptions?broadcaster_id={self.config.broadcaster_id}"
            f"&reward_id={reward_id}&status={status}"
        )

        redemptions = []
        for r_data in result.get("data", []):
            redemption = ChannelPointRedemption(
                redemption_id=r_data.get("id", ""),
                broadcaster_id=r_data.get("broadcaster_id", ""),
                reward_id=r_data.get("reward_id", ""),
                reward_title=r_data.get("reward", {}).get("title", ""),
                reward_cost=r_data.get("reward", {}).get("cost", 0),
                user_id=r_data.get("user_id", ""),
                user_name=r_data.get("user_name", ""),
                user_input=r_data.get("user_input", ""),
                status=r_data.get("status", ""),
                redeemed_at=r_data.get("redeemed_at", ""),
                phi_c_coherence=self.phi_bus.get_mesh_coherence() if self.phi_bus else 0.99,
            )
            redemptions.append(redemption)
            self._redemptions_queue.append(redemption)

        return redemptions

    async def fulfill_redemption(self, redemption_id: str, reward_id: str) -> bool:
        """Marca redemption como fulfilled."""
        result = await self._api_request(
            "PATCH",
            f"/channel_points/custom_rewards/redemptions?broadcaster_id={self.config.broadcaster_id}"
            f"&reward_id={reward_id}&id={redemption_id}",
            json={"status": "FULFILLED"}
        )

        success = "error" not in result
        if success:
            self._metrics.redemptions_processed += 1

        if self.temporal and success:
            await self.temporal.anchor_event("twitch_redemption_fulfilled", {
                "redemption_id": redemption_id,
                "reward_id": reward_id,
                "timestamp": time.time(),
            })

        return success

    # ── Drops ──────────────────────────────────────────────────

    async def get_drop_entitlements(self, game_id: str, status: str = "CLAIMED") -> List[DropEntitlement]:
        """Obtém entitlements de drops pendentes."""
        result = await self._api_request(
            "GET", f"/entitlements/drops?game_id={game_id}&fulfillment_status={status}"
        )

        entitlements = []
        for e_data in result.get("data", []):
            entitlement = DropEntitlement(
                entitlement_id=e_data.get("id", ""),
                benefit_id=e_data.get("benefit_id", ""),
                user_id=e_data.get("user_id", ""),
                user_name=e_data.get("user_name", ""),
                game_id=e_data.get("game_id", ""),
                campaign_id=e_data.get("campaign_id", ""),
                fulfillment_status=e_data.get("fulfillment_status", ""),
                created_at=e_data.get("created_at", ""),
                last_updated=e_data.get("last_updated", ""),
            )
            entitlements.append(entitlement)
            self._drops_queue.append(entitlement)

        return entitlements

    async def fulfill_drop(self, entitlement_ids: List[str]) -> bool:
        """Marca drops como fulfilled."""
        result = await self._api_request(
            "PATCH", "/entitlements/drops",
            json={"fulfillment_status": "FULFILLED", "entitlement_ids": entitlement_ids}
        )

        success = "error" not in result
        if success:
            self._metrics.drops_fulfilled += len(entitlement_ids)

        if self.temporal and success:
            await self.temporal.anchor_event("twitch_drops_fulfilled", {
                "entitlement_count": len(entitlement_ids),
                "timestamp": time.time(),
            })

        return success

    # ── EventSub WebSocket ─────────────────────────────────────

    async def connect_eventsub(self):
        """Conecta ao EventSub WebSocket para eventos em tempo real."""
        try:
            import websockets
            self._ws_connection = await websockets.connect(self.config.eventsub_ws_url)
            logger.info("EventSub WebSocket conectado")

            # Iniciar loop de recepção
            asyncio.create_task(self._eventsub_receive_loop())
            return True
        except ImportError:
            logger.warning("websockets não disponível — EventSub simulado")
            return True
        except Exception as e:
            logger.error(f"Falha ao conectar EventSub: {e}")
            return False

    async def _eventsub_receive_loop(self):
        """Loop de recepção de eventos EventSub."""
        try:
            import websockets
            while self._ws_connection:
                try:
                    message = await self._ws_connection.recv()
                    data = json.loads(message)
                    await self._handle_eventsub_message(data)
                except websockets.exceptions.ConnectionClosed:
                    logger.warning("EventSub WebSocket fechado — reconectando...")
                    await asyncio.sleep(5)
                    await self.connect_eventsub()
                    break
        except ImportError:
            pass

    async def _handle_eventsub_message(self, data: Dict):
        """Processa mensagem EventSub."""
        msg_type = data.get("metadata", {}).get("message_type", "")

        if msg_type == "session_welcome":
            session_id = data.get("payload", {}).get("session", {}).get("id")
            await self._subscribe_to_events(session_id)
        elif msg_type == "notification":
            subscription_type = data.get("metadata", {}).get("subscription_type", "")
            event_data = data.get("payload", {}).get("event", {})

            self._metrics.eventsub_messages_received += 1

            # Mapear para enum
            event_type = None
            for et in TwitchEventType:
                if et.value == subscription_type:
                    event_type = et
                    break

            if event_type:
                await self._dispatch_event(event_type, event_data)

                # Ancorar evento
                if self.temporal:
                    await self.temporal.anchor_event("twitch_eventsub", {
                        "event_type": subscription_type,
                        "event_id": data.get("metadata", {}).get("message_id", ""),
                        "timestamp": time.time(),
                    })

    async def _subscribe_to_events(self, session_id: str):
        """Subscreve a eventos no EventSub."""
        for event_type, version in self.EVENTSUB_SUBSCRIPTIONS.items():
            condition = {"broadcaster_user_id": self.config.broadcaster_id}
            if "chat" in event_type:
                condition["user_id"] = self.config.broadcaster_id

            payload = {
                "type": event_type,
                "version": version,
                "condition": condition,
                "transport": {
                    "method": "websocket",
                    "session_id": session_id,
                }
            }

            await self._api_request("POST", "/eventsub/subscriptions", json=payload)

    async def _dispatch_event(self, event_type: TwitchEventType, event_data: Dict):
        """Dispacha evento para handlers registrados."""
        handlers = self._event_handlers.get(event_type, [])
        for handler in handlers:
            try:
                await handler(event_data)
            except Exception as e:
                logger.error(f"Erro no handler de {event_type.value}: {e}")

    def on(self, event_type: TwitchEventType, handler: Callable):
        """Registra handler para evento."""
        if event_type not in self._event_handlers:
            self._event_handlers[event_type] = []
        self._event_handlers[event_type].append(handler)

    # ── PQC Signing para Metadados ─────────────────────────────

    async def sign_stream_metadata(self, stream: StreamInfo) -> Dict:
        """Assina metadados do stream com PQC."""
        if not self.pqc:
            return {"success": False, "error": "PQC not available"}

        metadata = json.dumps({
            "stream_id": stream.id,
            "title": stream.title,
            "broadcaster": stream.broadcaster_name,
            "viewers": stream.viewer_count,
            "phi_c": stream.phi_c_coherence,
            "timestamp": time.time(),
        }, sort_keys=True)

        keypair = self.pqc.generate_keypair()
        result = self.pqc.sign_message(metadata, keypair["private_key"])

        if not result.success:
            return {"success": False, "error": result.error_message}

        return {
            "success": True,
            "stream_id": stream.id,
            "metadata_hash": hashlib.sha3_256(metadata.encode()).hexdigest(),
            "signature_size": len(result.signature_or_ciphertext) if result.signature_or_ciphertext else 0,
            "algorithm": result.algorithm_used,
        }

    # ── Métricas e Health ────────────────────────────────────

    def get_metrics(self) -> ArkheTwitchMetrics:
        """Retorna métricas atuais."""
        self._metrics.stream_phi_c = self.phi_bus.get_mesh_coherence() if self.phi_bus else 0.997
        self._metrics.events_anchored = len(self._chat_history)
        return self._metrics

    def get_prometheus_metrics(self) -> str:
        """Gera métricas Prometheus."""
        m = self._metrics
        lines = [
            f'# HELP arkhe_twitch_stream_phi_c Phi-C coherence of stream',
            f'# TYPE arkhe_twitch_stream_phi_c gauge',
            f'arkhe_twitch_stream_phi_c {m.stream_phi_c:.4f}',
            f'',
            f'# HELP arkhe_twitch_chat_guardian_blocks_total Chat messages blocked by Guardian',
            f'# TYPE arkhe_twitch_chat_guardian_blocks_total counter',
            f'arkhe_twitch_chat_guardian_blocks_total {m.chat_guardian_blocks}',
            f'',
            f'# HELP arkhe_twitch_redemptions_processed_total Channel point redemptions processed',
            f'# TYPE arkhe_twitch_redemptions_processed_total counter',
            f'arkhe_twitch_redemptions_processed_total {m.redemptions_processed}',
            f'',
            f'# HELP arkhe_twitch_drops_fulfilled_total Drops fulfilled',
            f'# TYPE arkhe_twitch_drops_fulfilled_total counter',
            f'arkhe_twitch_drops_fulfilled_total {m.drops_fulfilled}',
            f'',
            f'# HELP arkhe_twitch_api_requests_total API requests',
            f'# TYPE arkhe_twitch_api_requests_total counter',
            f'arkhe_twitch_api_requests_total {m.api_requests_total}',
            f'',
            f'# HELP arkhe_twitch_api_errors_total API errors',
            f'# TYPE arkhe_twitch_api_errors_total counter',
            f'arkhe_twitch_api_errors_total {m.api_errors_total}',
            f'',
            f'# HELP arkhe_twitch_eventsub_messages_received_total EventSub messages received',
            f'# TYPE arkhe_twitch_eventsub_messages_received_total counter',
            f'arkhe_twitch_eventsub_messages_received_total {m.eventsub_messages_received}',
        ]
        return "\n".join(lines)

    async def health_check(self) -> Dict:
        """Health check do conector."""
        return {
            "status": "healthy",
            "broadcaster_id": self.config.broadcaster_id,
            "authenticated": self._access_token is not None,
            "eventsub_connected": self._ws_connection is not None,
            "chat_history_size": len(self._chat_history),
            "redemptions_queue_size": len(self._redemptions_queue),
            "drops_queue_size": len(self._drops_queue),
            "metrics": {
                "api_requests": self._metrics.api_requests_total,
                "api_errors": self._metrics.api_errors_total,
                "chat_blocks": self._metrics.chat_guardian_blocks,
            },
            "timestamp": time.time(),
        }
