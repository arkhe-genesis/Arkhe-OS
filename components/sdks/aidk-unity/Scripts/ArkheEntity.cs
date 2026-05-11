using UnityEngine;

namespace Arkhe.AIDK
{
    public class ArkheEntity : MonoBehaviour
    {
        [SerializeField] private string entityId;
        [SerializeField] private Renderer targetRenderer;
        [SerializeField] private Color healthyColor = Color.cyan;
        [SerializeField] private Color anomalyColor = Color.red;
        [SerializeField] private Light statusLight;

        private Material _instancedMaterial;

        void Start()
        {
            if (targetRenderer != null)
                _instancedMaterial = targetRenderer.material;

            if (string.IsNullOrEmpty(entityId))
                entityId = gameObject.name;

            ArkheManager.Instance.RegisterEntity(entityId, this);
        }

        public void ApplyState(EntityState state)
        {
            // Sync position if required by the game logic
            // transform.position = state.position;

            if (state.status == "anomaly_detected")
            {
                SetVisualState(anomalyColor, true);
            }
            else
            {
                SetVisualState(healthyColor, false);
            }
        }

        private void SetVisualState(Color color, bool isAnomaly)
        {
            if (_instancedMaterial != null)
                _instancedMaterial.color = color;

            if (statusLight != null)
            {
                statusLight.color = color;
                statusLight.intensity = isAnomaly ? 2.0f : 1.0f;
            }
        }
    }
}
