from flask import Flask, request, jsonify
import numpy as np, tensorflow as tf

app = Flask(__name__)
global_weights = None  # seria carregado do modelo inicial

@app.route('/tiny/upload', methods=['POST'])
def upload_gradients():
    data = request.get_json()
    node_id = data['node']
    grads = np.array(data['gradients'])
    # Agregar com FedAvg
    global global_weights
    if global_weights is None:
        global_weights = grads
    else:
        global_weights = global_weights * 0.9 + grads * 0.1
    # Salvar e retornar novo modelo se necessário
    return jsonify({"status": "ok", "round": len(global_weights)})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8088)
