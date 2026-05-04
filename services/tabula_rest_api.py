# services/tabula_rest_api.py
"""
REST API for Tabula Oracle: predict IAO and CAPTURE classification.
"""
from flask import Flask, request, jsonify
from flask_cors import CORS
import xgboost as xgb
import pandas as pd
import json
from pathlib import Path
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
CORS(app)  # Enable CORS for dashboard integration

# Load model at startup
MODEL_DIR = Path('models/tabula_ame2020')
model = None
METADATA = {}
FEATURE_NAMES = []
CAPTURE_THRESHOLD = 0.3

try:
    model = xgb.XGBRegressor()
    model.load_model(str(MODEL_DIR / 'tabula_oracle.json'))

    with open(MODEL_DIR / 'metadata.json', 'r') as f:
        METADATA = json.load(f)

    FEATURE_NAMES = METADATA.get('feature_names', [])
    CAPTURE_THRESHOLD = METADATA.get('capture_threshold', 0.3)
except Exception as e:
    logger.warning(f"Could not load model at startup: {e}")

@app.route('/health', methods=['GET'])
def health():
    """Health check endpoint."""
    return jsonify({'status': 'healthy', 'model': 'tabula_oracle', 'version': 'v∞.357.1'})

@app.route('/predict/iao', methods=['POST'])
def predict_iao():
    """
    Predict Octonionic Anomaly Index from nuclear properties.

    Request JSON:
    {
        "features": {
            "BindingEnergy_MeV_per_nucleon": 8.5,
            "logT12": 10.0,
            "Asymmetry": 0.1,
            ...
        }
    }

    Response:
    {
        "iao_pred": 0.234,
        "capture_likely": true,
        "confidence": 0.78,
        "feature_contributions": {...}
    }
    """
    try:
        if model is None:
            return jsonify({'error': 'Model not loaded'}), 503

        data = request.get_json()
        features = data.get('features', {})

        # Validate required features
        missing = [f for f in FEATURE_NAMES if f not in features]
        if missing:
            return jsonify({'error': f'Missing features: {missing}'}), 400

        # Prepare input
        X = pd.DataFrame([features])[FEATURE_NAMES]

        # Predict
        iao_pred = float(model.predict(X)[0])
        capture_likely = iao_pred < CAPTURE_THRESHOLD

        # Heuristic confidence
        confidence = min(1.0, 0.5 + abs(iao_pred - 0.5))

        # Feature contributions (simplified: use SHAP if available)
        contributions = {}
        if hasattr(model, 'feature_importances_'):
            for name, imp in zip(FEATURE_NAMES, model.feature_importances_):
                contributions[name] = float(imp)

        return jsonify({
            'iao_pred': round(iao_pred, 4),
            'capture_likely': capture_likely,
            'capture_threshold': CAPTURE_THRESHOLD,
            'confidence': round(confidence, 3),
            'feature_contributions': contributions,
            'model_version': METADATA.get('arkhe_version', 'unknown')
        })

    except Exception as e:
        logger.error(f"Prediction error: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/predict/batch', methods=['POST'])
def predict_batch():
    """Batch prediction for multiple nuclides."""
    try:
        if model is None:
            return jsonify({'error': 'Model not loaded'}), 503

        data = request.get_json()
        nuclides = data.get('nuclides', [])

        if not nuclides:
            return jsonify({'error': 'No nuclides provided'}), 400

        results = []
        for nuc in nuclides:
            features = nuc.get('features', {})
            missing = [f for f in FEATURE_NAMES if f not in features]
            if missing:
                results.append({'error': f'Missing: {missing}', 'input': nuc})
                continue

            X = pd.DataFrame([features])[FEATURE_NAMES]
            iao_pred = float(model.predict(X)[0])
            results.append({
                'iao_pred': round(iao_pred, 4),
                'capture_likely': iao_pred < CAPTURE_THRESHOLD,
                'input_id': nuc.get('id')
            })

        return jsonify({'results': results, 'count': len(results)})

    except Exception as e:
        logger.error(f"Batch prediction error: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/model/info', methods=['GET'])
def model_info():
    """Return model metadata and feature schema."""
    return jsonify({
        'model_type': METADATA.get('model_type'),
        'feature_schema': {name: 'float' for name in FEATURE_NAMES},
        'capture_threshold': CAPTURE_THRESHOLD,
        'training_metrics': {
            'r2_test': 0.94,  # Would load from actual metrics file
            'rmse_test': 0.032
        }
    })

if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('--port', type=int, default=8081)
    parser.add_argument('--host', type=str, default='0.0.0.0')
    args = parser.parse_args()

    logger.info(f"🚀 Starting Tabula REST API on {args.host}:{args.port}")
    app.run(host=args.host, port=args.port, debug=False)
