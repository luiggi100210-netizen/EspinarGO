import 'package:dio/dio.dart';
import 'package:flutter/foundation.dart';
import 'package:flutter_secure_storage/flutter_secure_storage.dart';
import '../constants/api_constants.dart';
import '../constants/storage_keys.dart';

/// Interceptor de Dio que maneja automáticamente:
/// - Agregar el token JWT a cada request
/// - Renovar el token cuando expira (401)
/// - Manejar errores de red
/// - Redirigir al login si la sesión expiró
class ApiInterceptor extends Interceptor {
  final FlutterSecureStorage _secureStorage = const FlutterSecureStorage();
  final void Function()? onSessionExpired;

  ApiInterceptor({this.onSessionExpired});

  @override
  void onRequest(RequestOptions options, RequestInterceptorHandler handler) async {
    // Obtener access_token y agregar al header
    final accessToken = await _secureStorage.read(key: StorageKeys.ACCESS_TOKEN);
    if (accessToken != null) {
      options.headers['Authorization'] = 'Bearer $accessToken';
    }
    handler.next(options);
  }

  @override
  void onError(DioException err, ErrorInterceptorHandler handler) async {
    final statusCode = err.response?.statusCode;

    // 401 - Token expirado, intentar renovar
    if (statusCode == 401) {
      final refreshToken = await _secureStorage.read(key: StorageKeys.REFRESH_TOKEN);
      
      if (refreshToken == null) {
        // No hay refresh token, ir al login
        await _clearSessionAndGoLogin();
        return handler.next(err);
      }

      try {
        final refreshDio = Dio(BaseOptions(baseUrl: ApiConstants.BASE_URL));
        final response = await refreshDio.post(
          '${ApiConstants.AUTH}${ApiConstants.REFRESH_TOKEN}',
          data: {'refresh_token': refreshToken},
        );

        if (response.statusCode == 200) {
          final newAccessToken = response.data['access_token'] as String;
          await _secureStorage.write(
            key: StorageKeys.ACCESS_TOKEN,
            value: newAccessToken,
          );

          err.requestOptions.headers['Authorization'] = 'Bearer $newAccessToken';
          final retryResponse = await refreshDio.fetch(err.requestOptions);
          return handler.resolve(retryResponse);
        }
      } catch (e) {
        await _clearSessionAndGoLogin();
      }
    }

    // 403 - Sin permisos
    if (statusCode == 403) {
      debugPrint('Sin permisos para esta acción');
    }

    // 500 - Error del servidor
    if (statusCode == 500) {
      debugPrint('Error del servidor: ${err.message}');
    }

    handler.next(err);
  }

  /// Limpia el storage y notifica al authProvider para redirigir al login.
  Future<void> _clearSessionAndGoLogin() async {
    await _secureStorage.delete(key: StorageKeys.ACCESS_TOKEN);
    await _secureStorage.delete(key: StorageKeys.REFRESH_TOKEN);
    onSessionExpired?.call();
  }
}