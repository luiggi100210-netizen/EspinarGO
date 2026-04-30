import 'package:flutter/foundation.dart';

/// Utilidad para imprimir logs en consola durante desarrollo.
/// En producción no imprime nada.
class AppLogger {
  static void info(String message, {String? tag}) {
    if (kDebugMode) {
      print('ℹ️ [EspinarGo${tag != null ? '·$tag' : ''}] $message');
    }
  }

  static void error(String message, {Object? error, StackTrace? stack}) {
    if (kDebugMode) {
      print('❌ [EspinarGo] $message');
      if (error != null) print('Error: $error');
      if (stack != null) print('Stack: $stack');
    }
  }

  static void success(String message, {String? tag}) {
    if (kDebugMode) {
      print('✅ [EspinarGo${tag != null ? '·$tag' : ''}] $message');
    }
  }

  static void warning(String message) {
    if (kDebugMode) {
      print('⚠️ [EspinarGo] $message');
    }
  }

  static void network(String method, String url, {int? statusCode}) {
    if (kDebugMode) {
      print('🌐 $method $url → $statusCode');
    }
  }
}