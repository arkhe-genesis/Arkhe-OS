import 'dart:async';
import 'dart:convert';
import 'dart:math';
import 'package:flutter/services.dart';

/**
 * ARKHE OS — Substrato 409-NEXMON-CSI
 * Plugin Dart para WiFi CSI via Nexmon
 *
 * Arquiteto: Rafael Oliveira (ORCID: 0009-0005-2697-4668)
 */

class WiFiCSIPlugin {
  static const MethodChannel _channel = MethodChannel('com.arkhe.citizen/nexmon');
  static const EventChannel _frameChannel = EventChannel('com.arkhe.citizen/nexmon/stream');

  /// Stream de frames 802.11 capturados via Nexmon
  static Stream<NexmonFrame> get frameStream {
    return _frameChannel.receiveBroadcastStream().map((event) {
      return NexmonFrame.fromJson(Map<String, dynamic>.from(event));
    });
  }

  // ─── Prerequisitos ───

  static Future<NexmonPrerequisites> checkPrerequisites() async {
    try {
      final result = await _channel.invokeMethod<Map<dynamic, dynamic>>('checkPrerequisites');
      if (result == null) return NexmonPrerequisites.unsupported();

      final map = Map<String, dynamic>.from(result);
      return NexmonPrerequisites(
        hasRoot: map['hasRoot'] ?? false,
        hasNexutil: map['hasNexutil'] ?? false,
        hasDevice: map['hasDevice'] ?? false,
        chipFamily: map['chipFamily'] ?? 'unknown',
        ready: map['ready'] ?? false,
        needsMagiskModule: map['needsMagiskModule'] ?? false,
      );
    } catch (e) {
      return NexmonPrerequisites.unsupported();
    }
  }

  static Future<bool> get isReady async {
    final prereqs = await checkPrerequisites();
    return prereqs.ready;
  }

  // ─── Captura ───

  static Future<NexmonStartResult> startCapture({
    int channel = 6,
    int bandwidth = 20,
    String filter = '0x88',
  }) async {
    try {
      final result = await _channel.invokeMethod<Map<dynamic, dynamic>>('startCapture', {
        'channel': channel,
        'bandwidth': bandwidth,
        'filter': filter,
      });

      if (result == null) {
        return NexmonStartResult.error('Resposta nula do nativo');
      }

      final map = Map<String, dynamic>.from(result);

      if (map['status'] == 'started') {
        return NexmonStartResult.success(
          chip: map['chip'] ?? 'unknown',
          channel: map['channel'] ?? 6,
        );
      }

      return NexmonStartResult.error(map['message'] ?? 'Erro desconhecido');

    } on PlatformException catch (e) {
      return NexmonStartResult.error(
        e.message ?? 'Erro de plataforma',
        code: e.code,
      );
    }
  }

  static Future<void> stopCapture() async {
    await _channel.invokeMethod('stopCapture');
  }

  // ─── Deteccao de Particulas ───

  static Stream<ParticleDetection> get particleDetections {
    return frameStream.asyncMap((frame) async {
      final detection = _processFrame(frame);
      return detection;
    }).where((d) => d != null).cast<ParticleDetection>();
  }

  static ParticleDetection? _processFrame(NexmonFrame frame) {
    // Extrair metricas do frame
    final metrics = _extractMetrics(frame);

    // Assinaturas de particulas
    final signatures = {
      'muon': [0.8, 0.6, 0.4, 0.3, 0.2],
      'electron': [0.5, 0.7, 0.5, 0.3, 0.1],
      'photon': [0.3, 0.4, 0.5, 0.4, 0.3],
    };

    String bestMatch = 'unknown';
    double bestScore = 0.0;

    signatures.forEach((particle, signature) {
      final score = _correlate(metrics, signature);
      if (score > bestScore && score > 0.6) {
        bestScore = score;
        bestMatch = particle;
      }
    });

    if (bestMatch == 'unknown') return null;

    // Estimar energia a partir de RSSI e taxa
    final energy = frame.rssi.abs() * 100.0 * (frame.rate / 54.0);

    return ParticleDetection(
      particleType: bestMatch,
      confidence: bestScore,
      energyKeV: energy,
      timestampNs: frame.timestampNs,
      source: 'wifi_csi_nexmon',
      metadata: {
        'chipFamily': frame.chipFamily,
        'channel': frame.channel,
        'rssi': frame.rssi,
        'rate': frame.rate,
      },
    );
  }

  static List<double> _extractMetrics(NexmonFrame frame) {
    // Usar comprimento do frame como proxy para assinatura
    final length = frame.rawDataLength;
    final bins = 5;
    final profile = List<double>.filled(bins, 0.0);

    // Distribuir comprimento em bins logaritmicos
    for (int i = 0; i < bins; i++) {
      final threshold = pow(2, i + 7).toDouble(); // 128, 256, 512, 1024, 2048
      profile[i] = length >= threshold ? 1.0 : length / threshold;
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
    return numerator / sqrt(denomA * denomB);
  }

  static double sqrt(double x) {
    if (x <= 0) return 0.0;
    var n = x;
    for (var i = 0; i < 10; i++) {
      n = (n + x / n) / 2;
    }
    return n;
  }

  static Future<Map<String, dynamic>> getChipInfo() async {
    try {
      final result = await _channel.invokeMethod<Map<dynamic, dynamic>>('getChipInfo');
      return Map<String, dynamic>.from(result ?? {});
    } catch (e) {
      return {'chipFamily': 'unknown', 'detected': false};
    }
  }
}

// ─── Modelos ───

class NexmonPrerequisites {
  final bool hasRoot;
  final bool hasNexutil;
  final bool hasDevice;
  final String chipFamily;
  final bool ready;
  final bool needsMagiskModule;

  NexmonPrerequisites({
    required this.hasRoot,
    required this.hasNexutil,
    required this.hasDevice,
    required this.chipFamily,
    required this.ready,
    required this.needsMagiskModule,
  });

  factory NexmonPrerequisites.unsupported() {
    return NexmonPrerequisites(
      hasRoot: false,
      hasNexutil: false,
      hasDevice: false,
      chipFamily: 'unknown',
      ready: false,
      needsMagiskModule: false,
    );
  }

  Map<String, dynamic> toJson() => {
    'hasRoot': hasRoot,
    'hasNexutil': hasNexutil,
    'hasDevice': hasDevice,
    'chipFamily': chipFamily,
    'ready': ready,
    'needsMagiskModule': needsMagiskModule,
  };
}

class NexmonStartResult {
  final bool success;
  final String? chip;
  final int? channel;
  final String? errorMessage;
  final String? errorCode;

  NexmonStartResult._({
    required this.success,
    this.chip,
    this.channel,
    this.errorMessage,
    this.errorCode,
  });

  factory NexmonStartResult.success({required String chip, required int channel}) {
    return NexmonStartResult._(success: true, chip: chip, channel: channel);
  }

  factory NexmonStartResult.error(String message, {String? code}) {
    return NexmonStartResult._(success: false, errorMessage: message, errorCode: code);
  }
}

class NexmonFrame {
  final int timestampNs;
  final String chipFamily;
  final int channel;
  final int rssi;
  final String macAddress;
  final String frameType;
  final int rate;
  final int rawDataLength;

  NexmonFrame({
    required this.timestampNs,
    required this.chipFamily,
    required this.channel,
    required this.rssi,
    required this.macAddress,
    required this.frameType,
    required this.rate,
    required this.rawDataLength,
  });

  factory NexmonFrame.fromJson(Map<String, dynamic> json) {
    return NexmonFrame(
      timestampNs: json['timestampNs'] ?? 0,
      chipFamily: json['chipFamily'] ?? 'unknown',
      channel: json['channel'] ?? 6,
      rssi: json['rssi'] ?? -50,
      macAddress: json['macAddress'] ?? '00:00:00:00:00:00',
      frameType: json['frameType'] ?? 'unknown',
      rate: json['rate'] ?? 0,
      rawDataLength: json['rawDataLength'] ?? 0,
    );
  }
}

class ParticleDetection {
  final String particleType;
  final double confidence;
  final double energyKeV;
  final int timestampNs;
  final String source;
  final Map<String, dynamic> metadata;

  ParticleDetection({
    required this.particleType,
    required this.confidence,
    required this.energyKeV,
    required this.timestampNs,
    required this.source,
    required this.metadata,
  });

  Map<String, dynamic> toJson() => {
    'particleType': particleType,
    'confidence': confidence,
    'energyKeV': energyKeV,
    'timestampNs': timestampNs,
    'source': source,
    'metadata': metadata,
  };
}