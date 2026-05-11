using System;
using System.Collections.Concurrent;
using System.Net.WebSockets;
using System.Text;
using System.Threading;
using System.Threading.Tasks;
using UnityEngine;

namespace Arkhe.AIDK
{
    public class ArkheWebSocketClient
    {
        private ClientWebSocket _webSocket;
        private readonly Uri _serverUri;
        private readonly string _authToken;
        private CancellationTokenSource _cancelTokenSource;

        private ConcurrentQueue<string> _outgoingMessages = new ConcurrentQueue<string>();

        public event Action<string> OnMessageReceived;
        public event Action OnConnected;
        public event Action<string> OnError;

        public ArkheWebSocketClient(string url, string token)
        {
            _serverUri = new Uri(url);
            _authToken = token;
            _webSocket = new ClientWebSocket();
            _webSocket.Options.SetRequestHeader("Authorization", $"Bearer {_authToken}");
        }

        public async Task Connect()
        {
            _cancelTokenSource = new CancellationTokenSource();
            try
            {
                await _webSocket.ConnectAsync(_serverUri, _cancelTokenSource.Token);
                Debug.Log("[Arkhe] Conectado ao Plano Etéreo (Stream Gateway).");
                OnConnected?.Invoke();

                _ = Task.Run(ReceiveLoop);
                _ = Task.Run(SendLoop);
            }
            catch (Exception e)
            {
                Debug.LogError($"[Arkhe] Falha na conexão WebSocket: {e.Message}");
                OnError?.Invoke(e.Message);
            }
        }

        private async Task ReceiveLoop()
        {
            var buffer = new byte[8192];
            while (_webSocket.State == WebSocketState.Open && !_cancelTokenSource.IsCancellationRequested)
            {
                var result = await _webSocket.ReceiveAsync(new ArraySegment<byte>(buffer), _cancelTokenSource.Token);
                if (result.MessageType == WebSocketMessageType.Text)
                {
                    var message = Encoding.UTF8.GetString(buffer, 0, result.Count);
                    OnMessageReceived?.Invoke(message);
                }
                else if (result.MessageType == WebSocketMessageType.Close)
                {
                    await _webSocket.CloseAsync(WebSocketCloseStatus.NormalClosure, "Server closed", CancellationToken.None);
                }
            }
        }

        private async Task SendLoop()
        {
            while (_webSocket.State == WebSocketState.Open && !_cancelTokenSource.IsCancellationRequested)
            {
                if (_outgoingMessages.TryDequeue(out var message))
                {
                    var bytes = Encoding.UTF8.GetBytes(message);
                    await _webSocket.SendAsync(new ArraySegment<byte>(bytes), WebSocketMessageType.Text, true, _cancelTokenSource.Token);
                }
                await Task.Delay(50);
            }
        }

        public void SendEvent(string jsonEvent)
        {
            _outgoingMessages.Enqueue(jsonEvent);
        }

        public async Task Disconnect()
        {
            if (_cancelTokenSource != null)
                _cancelTokenSource.Cancel();

            if (_webSocket != null && _webSocket.State == WebSocketState.Open)
                await _webSocket.CloseAsync(WebSocketCloseStatus.NormalClosure, "Fim da Sessão", CancellationToken.None);
        }
    }
}
