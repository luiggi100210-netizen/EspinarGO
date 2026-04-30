import 'package:dio/dio.dart';
import 'package:flutter/foundation.dart';
import '../constants/app_constants.dart';
import '../constants/api_constants.dart';
import 'api_interceptor.dart';

/// Configuración central de Dio para todas las llamadas a la API.
class DioClient {
  final Dio _dio;

  DioClient() : _dio = Dio(
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
    _dio.interceptors.add(ApiInterceptor());
    
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
  }) async {
    try {
      return await _dio.get(
        url,
        queryParameters: queryParameters,
        options: options,
      );
    } on DioException {
      rethrow;
    }
  }

  /// POST request
  Future<Response> post(
    String url, {
    dynamic data,
    Options? options,
  }) async {
    try {
      return await _dio.post(
        url,
        data: data,
        options: options,
      );
    } on DioException {
      rethrow;
    }
  }

  /// PUT request
  Future<Response> put(
    String url, {
    dynamic data,
    Options? options,
  }) async {
    try {
      return await _dio.put(
        url,
        data: data,
        options: options,
      );
    } on DioException {
      rethrow;
    }
  }

  /// PATCH request
  Future<Response> patch(
    String url, {
    dynamic data,
    Options? options,
  }) async {
    try {
      return await _dio.patch(
        url,
        data: data,
        options: options,
      );
    } on DioException {
      rethrow;
    }
  }

  /// DELETE request
  Future<Response> delete(
    String url, {
    Options? options,
  }) async {
    try {
      return await _dio.delete(
        url,
        options: options,
      );
    } on DioException {
      rethrow;
    }
  }
}