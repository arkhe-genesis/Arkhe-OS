import 'dart:async';
import 'package:flutter/services.dart';

/**
 * ARKHE CITIZEN — Bridge Unificada (405-eSIM + 406-CSI)
 * Expõe métodos nativos para Flutter
 * Arquiteto: Rafael Oliveira (ORCID: 0009-0005-2697-4668)
 */

class ArkheNativeBridge {
  static const MethodChannel _esimChannel = MethodChannel('com.arkhe.citizen/esim');
  static const MethodChannel _csiChannel = MethodChannel('com.arkhe.citizen/csi');
  static const EventChannel _csiStream = EventChannel('com.arkhe.citizen/csi/stream');

  // ─── eSIM (Substrato 405) ───

  static Future<bool> isESIMSupported() async {
    try {
      return await _esimChannel.invokeMethod('isSupported') ?? false;
    } catch (e) {
      return false;
    }
  }

  static Future<Map<String, dynamic>> acquireESIMProfile({
    required String provider,
    required String paymentTxid,
    String country = 'auto',
  }) async {
    try {
      final result = await _esimChannel.invokeMethod('acquireProfile', {
        'provider': provider,
        'txid': paymentTxid,
        'country': country,
      });
      return Map<String, dynamic>.from(result);
    } on PlatformException catch (e) {
      return {
        'error': true,
        'code': e.code,
        'message': e.message,
        'recoverable': e.details?['recoverable'] ?? false,
      };
    }
  }

  static Future<Map<String, dynamic>> getESIMStatus() async {
    try {
      final result = await _esimChannel.invokeMethod('getStatus');
      return Map<String, dynamic>.from(result);
    } catch (e) {
      return {'hasActiveProfile': false, 'error': e.toString()};
    }
  }

  // ─── WiFi CSI (Substrato 406) ───

  static Future<Map<String, dynamic>> checkCSIPrerequisites() async {
    try {
      final result = await _csiChannel.invokeMethod('checkPrerequisites');
      return Map<String, dynamic>.from(result);
    } catch (e) {
      return {'hasRoot': false, 'deviceSupported': false, 'error': e.toString()};
    }
  }

  static Future<Map<String, dynamic>> startCSICapture({int sampleRateHz = 100}) async {
    try {
      final result = await _csiChannel.invokeMethod('startCapture', {
        'sampleRateHz': sampleRateHz,
      });
      return Map<String, dynamic>.from(result);
    } on PlatformException catch (e) {
      return {
        'error': true,
        'code': e.code,
        'message': e.message,
      };
    }
  }

  static Future<void> stopCSICapture() async {
    await _csiChannel.invokeMethod('stopCapture');
  }

  /// Stream de frames CSI em tempo real
  static Stream<Map<String, dynamic>> getCSIStream() {
    return _csiStream.receiveBroadcastStream().map((event) {
      return Map<String, dynamic>.from(event);
    });
  }

  // ─── Deteção de Partículas via CSI ───

  static Stream<ParticleCSIDetection> getParticleDetections() {
    return getCSIStream().asyncMap((frame) async {
      // Processar frame CSI para deteção de partículas
      final csiData = List<double>.from(frame['csiData'] ?? []);
      if (csiData.isEmpty) return null;

      final detection = _processCSIData(csiData);
      if (detection == null) return null;

      return ParticleCSIDetection(
        particleType: detection['type'],
        confidence: detection['confidence'],
        energyKeV: detection['energyKeV'],
        timestampNs: frame['timestampNs'] ?? 0,
        csiFrame: frame,
      );
    }).where((event) => event != null).cast<ParticleCSIDetection>();
  }

  static Map<String, dynamic>? _processCSIData(List<double> csiData) {
    // Algoritmo de correlação com assinaturas conhecidas
    final signatures = {
      'muon': [0.8, 0.6, 0.4, 0.3, 0.2],
      'electron': [0.5, 0.7, 0.5, 0.3, 0.1],
      'photon': [0.3, 0.4, 0.5, 0.4, 0.3],
    };

    // Extrair perfil de amplitude (5 bins)
    final profile = _extractProfile(csiData, 5);

    // Correlacionar com assinaturas
    String bestMatch = 'unknown';
    double bestScore = 0.0;

    signatures.forEach((particle, signature) {
      final score = _correlate(profile, signature);
      if (score > bestScore && score > 0.7) {
        bestScore = score;
        bestMatch = particle;
      }
    });

    if (bestMatch == 'unknown') return null;

    // Estimar energia
    final energy = csiData.map((v) => v * v).reduce((a, b) => a + b) * 10.0;

    return {
      'type': bestMatch,
      'confidence': bestScore,
      'energyKeV': energy,
    };
  }

  static List<double> _extractProfile(List<double> data, int bins) {
    final profile = List<double>.filled(bins, 0.0);
    final chunkSize = data.length ~/ bins;

    for (int i = 0; i < bins; i++) {
      final start = i * chunkSize;
      final end = (i + 1) * chunkSize;
      var sum = 0.0;
      for (int j = start; j < end && j < data.length; j++) {
        sum += data[j];
      }
      profile[i] = sum / (end - start);
    }

    // Normalizar
    final max = profile.reduce((a, b) => a > b ? a : b);
    return profile.map((v) => v / max).toList();
  }

  static double _correlate(List<double> a, List<double> b) {
    final meanA = a.reduce((x, y) => x + y) / a.length;
    final meanB = b.reduce((x, y) => x + y) / b.length;

    double numerator = 0.0;
    double denomA = 0.0;
    double denomB = 0.0;

    for (int i = 0; i < a.length; i++) {
      final diffA = a[i] - meanA;
      final diffB = b[i] - meanB;
      numerator += diffA * diffB;
      denomA += diffA * diffA;
      denomB += diffB * diffB;
    }

    if (denomA <= 0 || denomB <= 0) return 0.0;
    return numerator / (denomA * denomB).sqrt();
  }
}

class ParticleCSIDetection {
  final String particleType;
  final double confidence;
  final double energyKeV;
  final int timestampNs;
  final Map<String, dynamic> csiFrame;

  ParticleCSIDetection({
    required this.particleType,
    required this.confidence,
    required this.energyKeV,
    required this.timestampNs,
    required this.csiFrame,
  });

  Map<String, dynamic> toJson() => {
    'particleType': particleType,
    'confidence': confidence,
    'energyKeV': energyKeV,
    'timestampNs': timestampNs,
    'sensors': ['wifi_csi'],
  };
}

extension on double {
  double sqrt() => this <= 0 ? 0.0 : _sqrt(this);
  static double _sqrt(double x) {
    // Aproximação simples de sqrt
    var n = x;
    for (var i = 0; i < 10; i++) {
      n = (n + x / n) / 2;
    }
    return n;
  }
}
