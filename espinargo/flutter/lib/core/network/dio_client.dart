import 'package:dio/dio.dart';
import 'package:flutter/foundation.dart';
import '../constants/app_constants.dart';
import '../constants/api_constants.dart';
import 'api_interceptor.dart';

/// Configuración central de Dio para todas las llamadas a la API.
class DioClient {
  final Dio _dio;

  DioClient({void Function()? onSessionExpired}) : _dio = Dio(
    BaseOptions(
      baseUrl: ApiConstants.BASE_URL,
      connectTimeout: Duration(milliseconds: AppConstants.CONNECTION_TIMEOUT),
      receiveTimeout: Duration(milliseconds: AppConstants.RECEIVE_TIMEOUT),
      headers: {
        'Content-Type': 'application/json',
      },
    ),
  ) {
    // Agregar interceptor de autenticación y manejo de errores
    _dio.interceptors.add(ApiInterceptor(onSessionExpired: onSessionExpired));
    
    if (kDebugMode) {
      _dio.interceptors.add(
        LogInterceptor(
          request: true,
          requestHeader: false,
          requestBody: true,
          responseHeader: false,
          responseBody: true,
          error: true,
        ),
      );
    }
  }

  Dio get dio => _dio;

  /// GET request
  Future<Response> get(
    String url, {
    Map<String, dynamic>? queryParameters,
    Options? options,
  }) =>
      _dio.get(url, queryParameters: queryParameters, options: options);

  /// POST request
  Future<Response> post(
    String url, {
    dynamic data,
    Options? options,
  }) =>
      _dio.post(url, data: data, options: options);

  /// PUT request
  Future<Response> put(
    String url, {
    dynamic data,
    Options? options,
  }) =>
      _dio.put(url, data: data, options: options);

  /// PATCH request
  Future<Response> patch(
    String url, {
    dynamic data,
    Options? options,
  }) =>
      _dio.patch(url, data: data, options: options);

  /// DELETE request
  Future<Response> delete(
    String url, {
    Options? options,
  }) =>
      _dio.delete(url, options: options);

  /// Extrae el mensaje de error de un DioException.
  /// Usado por todos los repositorios para evitar duplicación.
  static String parseError(DioException e) {
    if (e.response?.data != null && e.response?.data is Map) {
      final data = e.response!.data as Map<String, dynamic>;
      if (data['detail'] != null) return data['detail'] as String;
      if (data['message'] != null) return data['message'] as String;
    }
    switch (e.response?.statusCode) {
      case 400:
        return 'Datos inválidos';
      case 401:
        return 'Credenciales incorrectas';
      case 403:
        return 'No tienes permiso para esto';
      case 404:
        return 'No encontrado';
      case 409:
        return 'Conflicto con el estado actual';
      case 429:
        return 'Demasiados intentos. Espera unos minutos.';
      case 500:
        return 'Error del servidor. Intenta más tarde.';
      default:
        return 'Sin conexión a internet';
    }
  }
}