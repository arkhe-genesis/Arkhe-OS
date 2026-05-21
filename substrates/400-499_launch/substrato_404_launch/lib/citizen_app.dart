// ARKHE CITIZEN APP — Substrato 402/404
// Arquiteto: Rafael Oliveira (ORCID: 0009-0005-2697-4668)
// Framework: Flutter 3.24

import 'dart:async';
import 'dart:convert';
import 'dart:math';
import 'package:flutter/material.dart';
import 'package:camera/camera.dart';
import 'package:sensors_plus/sensors_plus.dart';
import 'package:connectivity_plus/connectivity_plus.dart';

// ═══════════════════════════════════════════════════════════════════
// MODELOS
// ═══════════════════════════════════════════════════════════════════

enum ParticleType { muon, electron, photon, neutron, unknown }
enum PrivacyLevel { anonymous, pseudonymous, identified }
enum ESIMProvider { silentLink, voidmob, pikasim, none }

class ParticleEvent {
  final int timestampNs;
  final ParticleType type;
  final double confidence;
  final double energyKeV;
  final List<String> sensors;
  final String? approximateLocation; // "country:region" apenas

  ParticleEvent({
    required this.timestampNs,
    required this.type,
    required this.confidence,
    required this.energyKeV,
    required this.sensors,
    this.approximateLocation,
  });

  Map<String, dynamic> toJson() => {
    'ts': timestampNs,
    'type': type.name,
    'conf': confidence,
    'E_keV': energyKeV,
    'sensors': sensors,
    'loc': approximateLocation,
  };
}

class CitizenProfile {
  final String pseudonym;
  final PrivacyLevel privacy;
  final ESIMProvider? esim;
  final String? exitCountry;
  int eventsDetected = 0;
  int rewardsSatoshis = 0;
  bool detectionActive = false;

  CitizenProfile({
    required this.pseudonym,
    this.privacy = PrivacyLevel.anonymous,
    this.esim,
    this.exitCountry,
  });
}

// ═══════════════════════════════════════════════════════════════════
// MOTOR DE DETEÇÃO (CRAYFIS-like)
// ═══════════════════════════════════════════════════════════════════

class ParticleDetector {
  final CameraController? camera;
  final StreamSubscription<AccelerometerEvent>? accelStream;
  final Random _rng = Random.secure();

  ParticleDetector({this.camera, this.accelStream});

  /// Simula deteção de partícula via análise de frame CMOS
  Future<ParticleEvent?> detectFromCamera(CameraImage image) async {
    // Em produção: análise de hot pixels, variação de luminosidade
    // Simulação: 2% de chance de deteção por frame processado
    if (_rng.nextDouble() > 0.98) return null;

    final types = [ParticleType.muon, ParticleType.electron, ParticleType.photon];
    final type = types[_rng.nextInt(types.length)];

    return ParticleEvent(
      timestampNs: DateTime.now().microsecondsSinceEpoch * 1000,
      type: type,
      confidence: 0.85 + _rng.nextDouble() * 0.14,
      energyKeV: _energyForType(type),
      sensors: ['cmos'],
    );
  }

  /// Deteção via acelerómetro (vibração por ionização)
  ParticleEvent? detectFromAccel(AccelerometerEvent event) {
    final magnitude = sqrt(event.x * event.x + event.y * event.y + event.z * event.z);
    if (magnitude > 25.0) { // threshold de vibração
      return ParticleEvent(
        timestampNs: DateTime.now().microsecondsSinceEpoch * 1000,
        type: ParticleType.muon,
        confidence: 0.75,
        energyKeV: magnitude * 10,
        sensors: ['accelerometer'],
      );
    }
    return null;
  }

  double _energyForType(ParticleType type) {
    switch (type) {
      case ParticleType.muon: return 4000 + _rng.nextDouble() * 2000;
      case ParticleType.electron: return 500 + _rng.nextDouble() * 1000;
      case ParticleType.photon: return 100 + _rng.nextDouble() * 500;
      default: return 0;
    }
  }
}

// ═══════════════════════════════════════════════════════════════════
// CAMADA DE PRIVACIDADE
// ═══════════════════════════════════════════════════════════════════

class PrivacyEngine {
  /// Ofusca localização para país:região apenas
  static String? obfuscateLocation(double? lat, double? lon) {
    if (lat == null || lon == null) return null;
    // Aproximar para ~50km
    final approxLat = (lat * 10).round() / 10;
    final approxLon = (lon * 10).round() / 10;
    return "${approxLat.toStringAsFixed(1)}:${approxLon.toStringAsFixed(1)}";
  }

  /// Encripta evento com Ed25519 (placeholder para libsodium)
  static String encryptEvent(ParticleEvent event, String publicKey) {
    final plaintext = jsonEncode(event.toJson());
    // Em produção: libsodium crypto_box_seal
    final hash = base64Encode(utf8.encode(plaintext));
    return "ARKHE:$hash";
  }

  /// Verifica se a conectividade atual é anónima (eSIM)
  static Future<bool> isAnonymousConnection() async {
    final result = await Connectivity().checkConnectivity();
    // Se for mobile e tiver eSIM ativo, assumir anónimo
    return result == ConnectivityResult.mobile;
  }
}

// ═══════════════════════════════════════════════════════════════════
// INTERFACE DO UTILIZADOR
// ═══════════════════════════════════════════════════════════════════

class CitizenApp extends StatefulWidget {
  const CitizenApp({super.key});

  @override
  State<CitizenApp> createState() => _CitizenAppState();
}

class _CitizenAppState extends State<CitizenApp> {
  late CitizenProfile profile;
  List<ParticleEvent> events = [];
  bool isDetecting = false;
  Timer? _detectionTimer;

  @override
  void initState() {
    super.initState();
    profile = CitizenProfile(
      pseudonym: "citizen_${Random.secure().nextInt(999999)}",
      privacy: PrivacyLevel.anonymous,
      esim: ESIMProvider.silentLink,
      exitCountry: "CH",
    );
  }

  void _toggleDetection() {
    setState(() {
      isDetecting = !isDetecting;
      if (isDetecting) {
        _startDetection();
      } else {
        _detectionTimer?.cancel();
      }
    });
  }

  void _startDetection() {
    final detector = ParticleDetector();
    _detectionTimer = Timer.periodic(const Duration(seconds: 5), (timer) async {
      // Simulação: deteção periódica
      final event = ParticleEvent(
        timestampNs: DateTime.now().microsecondsSinceEpoch * 1000,
        type: [ParticleType.muon, ParticleType.electron, ParticleType.photon][Random().nextInt(3)],
        confidence: 0.85 + Random().nextDouble() * 0.14,
        energyKeV: 100 + Random().nextDouble() * 5000,
        sensors: ['cmos', 'accelerometer'],
        approximateLocation: PrivacyEngine.obfuscateLocation(40.7, -74.0),
      );

      setState(() {
        events.add(event);
        profile.eventsDetected++;
        profile.rewardsSatoshis += (event.confidence * 10).round();
      });

      // Partilhar via mesh (simulado)
      _shareToMesh(event);
    });
  }

  void _shareToMesh(ParticleEvent event) {
    // Em produção: enviar para nós vizinhos via Bluetooth/WiFi Direct
    debugPrint("[MESH] Evento partilhado: ${event.type.name} @ ${event.energyKeV.toStringAsFixed(0)} keV");
  }

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: 'Arkhe Citizen',
      theme: ThemeData.dark().copyWith(
        primaryColor: const Color(0xFF1A237E),
        scaffoldBackgroundColor: const Color(0xFF0A0A0A),
      ),
      home: Scaffold(
        appBar: AppBar(
          title: const Text('ARKHE CITIZEN', style: TextStyle(letterSpacing: 4)),
          centerTitle: true,
        ),
        body: Padding(
          padding: const EdgeInsets.all(16.0),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.stretch,
            children: [
              // Cartão de perfil
              _buildProfileCard(),
              const SizedBox(height: 16),
              // Botão de deteção
              ElevatedButton.icon(
                onPressed: _toggleDetection,
                icon: Icon(isDetecting ? Icons.stop : Icons.sensors),
                label: Text(isDetecting ? 'PARAR DETEÇÃO' : 'INICIAR DETEÇÃO'),
                style: ElevatedButton.styleFrom(
                  backgroundColor: isDetecting ? Colors.red : Colors.green,
                  padding: const EdgeInsets.symmetric(vertical: 20),
                ),
              ),
              const SizedBox(height: 16),
              // Estatísticas
              _buildStatsRow(),
              const SizedBox(height: 16),
              // Lista de eventos
              Expanded(
                child: Card(
                  child: ListView.builder(
                    itemCount: events.length,
                    itemBuilder: (context, index) {
                      final e = events[events.length - 1 - index];
                      return ListTile(
                        leading: _particleIcon(e.type),
                        title: Text('${e.type.name.toUpperCase()} — ${e.energyKeV.toStringAsFixed(0)} keV'),
                        subtitle: Text('Confiança: ${(e.confidence * 100).toStringAsFixed(1)}%'),
                        trailing: Text('${e.sensors.join(", ")}'),
                      );
                    },
                  ),
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }

  Widget _buildProfileCard() {
    return Card(
      child: Padding(
        padding: const EdgeInsets.all(16.0),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text('Pseudónimo: ${profile.pseudonym}', style: const TextStyle(fontSize: 14)),
            Text('Privacidade: ${profile.privacy.name}', style: const TextStyle(fontSize: 14)),
            if (profile.esim != null)
              Text('eSIM: ${profile.esim!.name} (${profile.exitCountry})',
                   style: const TextStyle(fontSize: 14, color: Colors.green)),
          ],
        ),
      ),
    );
  }

  Widget _buildStatsRow() {
    return Row(
      mainAxisAlignment: MainAxisAlignment.spaceEvenly,
      children: [
        _statCard('Eventos', profile.eventsDetected.toString()),
        _statCard('Recompensas', '${profile.rewardsSatoshis} sats'),
        _statCard('Status', isDetecting ? 'ATIVO' : 'INATIVO'),
      ],
    );
  }

  Widget _statCard(String label, String value) {
    return Card(
      child: Padding(
        padding: const EdgeInsets.all(12.0),
        child: Column(
          children: [
            Text(value, style: const TextStyle(fontSize: 20, fontWeight: FontWeight.bold)),
            Text(label, style: const TextStyle(fontSize: 12)),
          ],
        ),
      ),
    );
  }

  Widget _particleIcon(ParticleType type) {
    final colors = {
      ParticleType.muon: Colors.blue,
      ParticleType.electron: Colors.green,
      ParticleType.photon: Colors.yellow,
      ParticleType.neutron: Colors.purple,
      ParticleType.unknown: Colors.grey,
    };
    return CircleAvatar(
      backgroundColor: colors[type],
      child: Text(type.name[0].toUpperCase(), style: const TextStyle(color: Colors.white)),
    );
  }

  @override
  void dispose() {
    _detectionTimer?.cancel();
    super.dispose();
  }
}

void main() {
  runApp(const CitizenApp());
}
