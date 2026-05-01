// ARKHE BRIDGE UI v∞.290
#target aftereffects

(function(thisObj) {
    // ──────── UI ────────
    var win = (thisObj instanceof Panel) ? thisObj : new Window('palette', 'ARKHE Bridge', undefined);
    win.orientation = 'column';
    win.alignChildren = 'left';
    win.spacing = 5;

    // Grupo de conexão
    var grpConn = win.add('group');
    grpConn.add('statictext', undefined, 'Host:');
    var hostInput = grpConn.add('edittext', undefined, 'localhost');
    hostInput.characters = 10;
    grpConn.add('statictext', undefined, 'Porta:');
    var portInput = grpConn.add('edittext', undefined, '9999');
    portInput.characters = 6;
    var btnConnect = grpConn.add('button', undefined, 'Conectar');
    var statusText = win.add('statictext', undefined, 'Desconectado');

    // Grupo de alvo
    var grpTarget = win.add('panel', undefined, 'Propriedade Alvo');
    var targetLayerText = grpTarget.add('statictext', undefined, 'Nenhuma camada selecionada');
    var btnPickLayer = grpTarget.add('button', undefined, 'Selecionar Camada');
    var propList = grpTarget.add('dropdownlist', undefined, ['Posição', 'Escala', 'Rotação', 'Opacidade', 'Cor (Preenchimento)']);
    propList.selection = 0;
    var paramMap = grpTarget.add('dropdownlist', undefined, ['kappa', 'cBrain']);
    paramMap.selection = 0;
    var scaleLabel = grpTarget.add('statictext', undefined, 'Escala do valor (%):');
    var scaleInput = grpTarget.add('edittext', undefined, '100');
    scaleInput.characters = 5;

    // Botão de aplicar contínuo
    var btnApply = win.add('button', undefined, 'Aplicar Valores (Modo Contínuo)');
    var btnStop = win.add('button', undefined, 'Parar');

    var logText = win.add('edittext', undefined, '', {multiline: true, scrolling: true});
    logText.size = [300, 100];

    // ──────── LÓGICA DE CONEXÃO ────────
    var socket = null;
    var selectedLayer = null;
    var isRunning = false;

    function log(msg) { logText.text += msg + '\n'; }

    btnConnect.onClick = function() {
        if (socket && socket.connected) {
            socket.close();
            btnConnect.text = 'Conectar';
            statusText.text = 'Desconectado';
            log('Desconectado.');
            return;
        }
        try {
            socket = new Socket;
            if (socket.open(hostInput.text + ':' + portInput.text)) {
                socket.encoding = 'UTF-8';
                // Leitura assíncrona
                socket.onData = function(data) {
                    try {
                        var msgs = data.split('\n');
                        for (var i = 0; i < msgs.length; i++) {
                            if (msgs[i].length == 0) continue;
                            var obj = JSON.parse(msgs[i]);
                            if (isRunning) updateProperties(obj);
                        }
                    } catch(e) {
                        log('Erro JSON: ' + e.toString());
                    }
                };
                btnConnect.text = 'Desconectar';
                statusText.text = 'Conectado';
                log('Conectado ao bridge.');
            } else {
                log('Falha na conexão.');
                socket = null;
            }
        } catch(e) {
            log('Erro de socket: ' + e.toString());
        }
    };

    // Selecionar camada
    btnPickLayer.onClick = function() {
        var comp = app.project.activeItem;
        if (!comp || !(comp instanceof CompItem)) {
            alert('Selecione uma composição ativa.');
            return;
        }
        var selectedLayers = comp.selectedLayers;
        if (selectedLayers.length == 0) {
            alert('Selecione uma camada.');
            return;
        }
        selectedLayer = selectedLayers[0];
        targetLayerText.text = selectedLayer.name;
        log('Camada alvo: ' + selectedLayer.name);
    };

    function updateProperties(data) {
        if (!selectedLayer) return;
        var value = parseFloat(data[paramMap.selection.text]); // kappa ou cBrain
        if (isNaN(value)) return;
        // Aplicar escala
        var scale = parseFloat(scaleInput.text) / 100.0;
        value *= scale;

        var propIndex = propList.selection.index;
        var propName = '';
        switch (propIndex) {
            case 0: // Posição
                propName = 'Position';
                // Modificar apenas X ou Y? Vamos usar X = value*10 relativo ao centro.
                var pos = selectedLayer.property(propName);
                if (pos) {
                    var curVal = pos.value;
                    curVal[0] = 540 + value * 10; // centro 1080p
                    pos.setValue(curVal);
                }
                break;
            case 1: // Escala
                propName = 'Scale';
                var sval = [value, value];
                selectedLayer.property(propName).setValue(sval);
                break;
            case 2: // Rotação
                propName = 'Rotation';
                selectedLayer.property(propName).setValue(value);
                break;
            case 3: // Opacidade
                propName = 'Opacity';
                selectedLayer.property(propName).setValue(value);
                break;
            case 4: // Cor de preenchimento (apenas para shape layer ou fill effect)
                // Tentamos aplicar a Fill color da primeira camada de forma sólida
                try {
                    var solid = selectedLayer.property('ADBE Effect Parade').property('ADBE Fill');
                    if (solid) {
                        solid.property('ADBE Fill-0003').setValue([value/100.0, 0.5, 0.9, 1.0]);
                    }
                } catch(e) {}
                break;
        }
    }

    btnApply.onClick = function() { isRunning = true; log('Modo contínuo ativado.'); };
    btnStop.onClick = function() { isRunning = false; log('Parado.'); };

    win.layout.layout(true);
    if (win instanceof Window) {
        win.center();
        win.show();
    } else {
        win.layout.layout(true);
    }
})(this);
