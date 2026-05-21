import 'dart:async';
import 'dart:convert';
import 'package:flutter/services.dart';

/**
 * ARKHE OS — Substrato 408-ESIM-BRIDGE
 * Plugin Flutter esim_manager — Bridge completa para EuiccManager
 * Suporta: Silent Link, Voidmob, PikaSim
 *
 * Arquiteto: Rafael Oliveira (ORCID: 0009-0005-2697-4668)
 */

class ESIMManagerPlugin {
  static const MethodChannel _channel = MethodChannel('com.arkhe.citizen/esim_manager');
  static const EventChannel _statusChannel = EventChannel('com.arkhe.citizen/esim_manager/status');

  /// Stream de mudanças de estado do eSIM
  static Stream<Map<String, dynamic>> get esimStatusStream {
    return _statusChannel.receiveBroadcastStream().map((event) {
      return Map<String, dynamic>.from(event);
    });
  }

  // ─── Verificação de Suporte ───

  /// Verifica se o dispositivo suporta eSIM
  static Future<bool> isESIMSupported() async {
    try {
      final result = await _channel.invokeMethod<bool>('isESIMSupported');
      return result ?? false;
    } on PlatformException catch (e) {
      print('[ESIM] Erro ao verificar suporte: ${e.message}');
      return false;
    }
  }

  /// Verifica se há um LPA (Local Profile Assistant) ativo
  static Future<bool> hasActiveLPA() async {
    try {
      final result = await _channel.invokeMethod<bool>('hasActiveLPA');
      return result ?? false;
    } catch (e) {
      return false;
    }
  }

  // ─── Gestão de Perfis ───

  /// Lista perfis eSIM instalados no dispositivo
  static Future<List<ESIMProfile>> getInstalledProfiles() async {
    try {
      final result = await _channel.invokeMethod<List<dynamic>>('getInstalledProfiles');
      if (result == null) return [];
      return result.map((json) => ESIMProfile.fromJson(Map<String, dynamic>.from(json))).toList();
    } catch (e) {
      print('[ESIM] Erro ao listar perfis: $e');
      return [];
    }
  }

  /// Adquire e instala perfil de um provedor
  /// Fluxo: pagamento → obter activationCode → download via SM-DP+ → ativar
  static Future<ESIMActivationResult> acquireProfile({
    required ESIMProvider provider,
    required String paymentTxid,
    String country = 'auto',
    String dataPlan = '1GB_30D',
  }) async {
    try {
      final result = await _channel.invokeMethod<Map<dynamic, dynamic>>('acquireProfile', {
        'provider': provider.name,
        'providerConfigUrl': provider.configUrl,
        'paymentTxid': paymentTxid,
        'country': country,
        'dataPlan': dataPlan,
      });

      if (result == null) {
        return ESIMActivationResult.error('Resposta nula do nativo');
      }

      final map = Map<String, dynamic>.from(result);

      if (map['error'] == true) {
        return ESIMActivationResult.error(
          map['message'] ?? 'Erro desconhecido',
          code: map['code']?.toString(),
          recoverable: map['recoverable'] ?? false,
        );
      }

      return ESIMActivationResult.success(
        iccid: map['iccid'] ?? '',
        carrierName: map['carrierName'] ?? 'Unknown',
        activationCode: map['activationCode'] ?? '',
        profileStatus: map['profileStatus'] ?? 'UNKNOWN',
      );

    } on PlatformException catch (e) {
      return ESIMActivationResult.error(
        e.message ?? 'Erro de plataforma',
        code: e.code,
        recoverable: e.details?['recoverable'] ?? false,
      );
    }
  }

  /// Ativa um perfil eSIM específico
  static Future<bool> activateProfile(String iccid) async {
    try {
      final result = await _channel.invokeMethod<bool>('activateProfile', {'iccid': iccid});
      return result ?? false;
    } catch (e) {
      print('[ESIM] Erro ao ativar perfil: $e');
      return false;
    }
  }

  /// Desativa um perfil eSIM (preserva dados, desliga radio)
  static Future<bool> deactivateProfile(String iccid) async {
    try {
      final result = await _channel.invokeMethod<bool>('deactivateProfile', {'iccid': iccid});
      return result ?? false;
    } catch (e) {
      print('[ESIM] Erro ao desativar perfil: $e');
      return false;
    }
  }

  /// Elimina um perfil eSIM do dispositivo (irreversível)
  static Future<bool> deleteProfile(String iccid) async {
    try {
      final result = await _channel.invokeMethod<bool>('deleteProfile', {'iccid': iccid});
      return result ?? false;
    } catch (e) {
      print('[ESIM] Erro ao eliminar perfil: $e');
      return false;
    }
  }

  // ─── Estado de Conectividade ───

  /// Obtém estado de conectividade do perfil ativo
  static Future<ESIMConnectivityStatus> getConnectivityStatus() async {
    try {
      final result = await _channel.invokeMethod<Map<dynamic, dynamic>>('getConnectivityStatus');
      if (result == null) return ESIMConnectivityStatus.empty();

      final map = Map<String, dynamic>.from(result);
      return ESIMConnectivityStatus(
        hasActiveProfile: map['hasActiveProfile'] ?? false,
        activeProfiles: List<String>.from(map['activeProfiles'] ?? []),
        isAnonymous: map['isAnonymous'] ?? false,
        ipExitCountry: map['ipExitCountry'] ?? 'unknown',
        carrierName: map['carrierName'] ?? 'none',
        signalStrength: map['signalStrength'] ?? 0,
        dataUsedMB: map['dataUsedMB'] ?? 0.0,
      );
    } catch (e) {
      return ESIMConnectivityStatus.empty();
    }
  }

  /// Verifica se a conectividade atual é anónima (eSIM ativo)
  static Future<bool> isAnonymousConnection() async {
    final status = await getConnectivityStatus();
    return status.isAnonymous && status.hasActiveProfile;
  }

  // ─── Fluxo Completo de Ativação ───

  /// Fluxo completo: desde pagamento até perfil ativo
  static Future<ESIMActivationResult> fullActivationFlow({
    required ESIMProvider provider,
    required String paymentTxid,
    String country = 'auto',
    String dataPlan = '1GB_30D',
  }) async {
    // 1. Verificar suporte
    if (!await isESIMSupported()) {
      return ESIMActivationResult.error(
        'Dispositivo não suporta eSIM',
        code: 'DEVICE_NOT_SUPPORTED',
        recoverable: false,
      );
    }

    // 2. Verificar LPA
    if (!await hasActiveLPA()) {
      return ESIMActivationResult.error(
        'Nenhum LPA ativo no dispositivo',
        code: 'LPA_NOT_FOUND',
        recoverable: true,
      );
    }

    // 3. Adquirir perfil
    final acquireResult = await acquireProfile(
      provider: provider,
      paymentTxid: paymentTxid,
      country: country,
      dataPlan: dataPlan,
    );

    if (!acquireResult.success) {
      return acquireResult;
    }

    // 4. Ativar perfil
    final activated = await activateProfile(acquireResult.iccid!);
    if (!activated) {
      return ESIMActivationResult.error(
        'Perfil adquirido mas falha na ativação',
        code: 'ACTIVATION_FAILED',
        recoverable: true,
      );
    }

    return ESIMActivationResult.success(
      iccid: acquireResult.iccid!,
      carrierName: acquireResult.carrierName!,
      activationCode: acquireResult.activationCode!,
      profileStatus: 'ACTIVE',
    );
  }
}

// ─── Modelos de Dados ───

enum ESIMProvider {
  silentLink('https://api.silent.link/v1/esim', 'Silent Link', 160),
  voidmob('https://api.voidmob.io/v1/esim', 'Voidmob', 200),
  pikasim('https://api.pikasim.org/v1/esim', 'PikaSim', 80);

  final String configUrl;
  final String displayName;
  final int coverageCountries;

  const ESIMProvider(this.configUrl, this.displayName, this.coverageCountries);

  static ESIMProvider? fromString(String name) {
    return values.firstWhere(
      (p) => p.name.toLowerCase() == name.toLowerCase(),
      orElse: () => silentLink,
    );
  }
}

class ESIMProfile {
  final String iccid;
  final String carrierName;
  final String? activationCode;
  final String profileStatus;
  final bool isActive;
  final String? nickname;

  ESIMProfile({
    required this.iccid,
    required this.carrierName,
    this.activationCode,
    required this.profileStatus,
    required this.isActive,
    this.nickname,
  });

  factory ESIMProfile.fromJson(Map<String, dynamic> json) {
    return ESIMProfile(
      iccid: json['iccid'] ?? '',
      carrierName: json['carrierName'] ?? 'Unknown',
      activationCode: json['activationCode'],
      profileStatus: json['profileStatus'] ?? 'UNKNOWN',
      isActive: json['isActive'] ?? false,
      nickname: json['nickname'],
    );
  }

  Map<String, dynamic> toJson() => {
    'iccid': iccid,
    'carrierName': carrierName,
    'activationCode': activationCode,
    'profileStatus': profileStatus,
    'isActive': isActive,
    'nickname': nickname,
  };
}

class ESIMActivationResult {
  final bool success;
  final String? iccid;
  final String? carrierName;
  final String? activationCode;
  final String? profileStatus;
  final String? errorMessage;
  final String? errorCode;
  final bool recoverable;

  ESIMActivationResult._({
    required this.success,
    this.iccid,
    this.carrierName,
    this.activationCode,
    this.profileStatus,
    this.errorMessage,
    this.errorCode,
    this.recoverable = false,
  });

  factory ESIMActivationResult.success({
    required String iccid,
    required String carrierName,
    required String activationCode,
    required String profileStatus,
  }) {
    return ESIMActivationResult._(
      success: true,
      iccid: iccid,
      carrierName: carrierName,
      activationCode: activationCode,
      profileStatus: profileStatus,
    );
  }

  factory ESIMActivationResult.error(
    String message, {
    String? code,
    bool recoverable = false,
  }) {
    return ESIMActivationResult._(
      success: false,
      errorMessage: message,
      errorCode: code,
      recoverable: recoverable,
    );
  }

  @override
  String toString() {
    if (success) {
      return 'ESIMActivationResult(success, iccid=$iccid, carrier=$carrierName, status=$profileStatus)';
    }
    return 'ESIMActivationResult(error, code=$errorCode, message=$errorMessage, recoverable=$recoverable)';
  }
}

class ESIMConnectivityStatus {
  final bool hasActiveProfile;
  final List<String> activeProfiles;
  final bool isAnonymous;
  final String ipExitCountry;
  final String? carrierName;
  final int signalStrength;
  final double dataUsedMB;

  ESIMConnectivityStatus({
    required this.hasActiveProfile,
    required this.activeProfiles,
    required this.isAnonymous,
    required this.ipExitCountry,
    this.carrierName,
    required this.signalStrength,
    required this.dataUsedMB,
  });

  factory ESIMConnectivityStatus.empty() {
    return ESIMConnectivityStatus(
      hasActiveProfile: false,
      activeProfiles: [],
      isAnonymous: false,
      ipExitCountry: 'unknown',
      carrierName: null,
      signalStrength: 0,
      dataUsedMB: 0.0,
    );
  }

  Map<String, dynamic> toJson() => {
    'hasActiveProfile': hasActiveProfile,
    'activeProfiles': activeProfiles,
    'isAnonymous': isAnonymous,
    'ipExitCountry': ipExitCountry,
    'carrierName': carrierName,
    'signalStrength': signalStrength,
    'dataUsedMB': dataUsedMB,
  };
}
