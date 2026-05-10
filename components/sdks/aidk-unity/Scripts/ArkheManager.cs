using System.Collections.Concurrent;
using System.Collections.Generic;
using UnityEngine;

namespace Arkhe.AIDK
{
    public class ArkheManager : MonoBehaviour
    {
        public static ArkheManager Instance { get; private set; }

        [Header("Arkhe Configuration")]
        [SerializeField] private string serverUrl = "wss://api.arkhe.ai/api/v1/stream";
        [SerializeField] private string authToken = ""; // Should be set via code or inspector from a secure source

        private ArkheWebSocketClient _client;
        private ConcurrentQueue<string> _mainThreadMessageQueue = new ConcurrentQueue<string>();
        private Dictionary<string, ArkheEntity> _registeredEntities = new Dictionary<string, ArkheEntity>();

        void Awake()
        {
            if (Instance == null)
            {
                Instance = this;
                DontDestroyOnLoad(gameObject);
                if (!string.IsNullOrEmpty(authToken))
                {
                    InitializeClient();
                }
            }
            else
            {
                Destroy(gameObject);
            }
        }

        public void InitializeClient(string token = null)
        {
            if (token != null) authToken = token;
            if (string.IsNullOrEmpty(authToken))
            {
                Debug.LogError("[ArkheManager] Auth token is missing.");
                return;
            }

            _client = new ArkheWebSocketClient(serverUrl, authToken);
            _client.OnMessageReceived += (msg) => _mainThreadMessageQueue.Enqueue(msg);
            _client.OnConnected += () => Debug.Log("[ArkheManager] Real-time stream active.");
            _ = _client.Connect();
        }

        void Update()
        {
            while (_mainThreadMessageQueue.TryDequeue(out var message))
            {
                ProcessMessage(message);
            }
        }

        private void ProcessMessage(string json)
        {
            try {
                var update = JsonUtility.FromJson<ArkheStateUpdate>(json);
                if (update != null && update.entities != null)
                {
                    foreach (var entityState in update.entities)
                    {
                        if (_registeredEntities.TryGetValue(entityState.id, out var entity))
                        {
                            entity.ApplyState(entityState);
                        }
                    }
                }
            } catch (System.Exception e) {
                Debug.LogError($"[Arkhe] Error parsing state update: {e.Message}");
            }
        }

        public void RegisterEntity(string id, ArkheEntity entity)
        {
            _registeredEntities[id] = entity;
        }

        public void SendAction(string action, Vector3 pos)
        {
            if (_client == null) return;

            var evt = new PlayerActionEvent
            {
                game_id = "unity-aidk-demo",
                player_id = SystemInfo.deviceUniqueIdentifier,
                action = action,
                target = new TargetData { type = "coordinate", data = new CoordData { x = pos.x, y = pos.y, z = pos.z } }
            };
            _client.SendEvent(JsonUtility.ToJson(evt));
        }

        void OnDestroy()
        {
            if (_client != null)
                _ = _client.Disconnect();
        }
    }

    [System.Serializable]
    public class ArkheStateUpdate { public List<EntityState> entities; }

    [System.Serializable]
    public class EntityState
    {
        public string id;
        public string status;
        public string severity;
        public Vector3 position;
    }

    [System.Serializable]
    public class PlayerActionEvent
    {
        public string game_id;
        public string player_id;
        public string action;
        public TargetData target;
    }

    [System.Serializable]
    public class TargetData { public string type; public CoordData data; }

    [System.Serializable]
    public class CoordData { public float x; public float y; public float z; }
}
