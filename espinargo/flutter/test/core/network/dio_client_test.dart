import 'package:dio/dio.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:espinargo_app/core/network/dio_client.dart';

/// Helper: crea un DioException con un statusCode y body dados.
DioException _makeError({
  int? statusCode,
  Map<String, dynamic>? data,
}) {
  final opts = RequestOptions(path: '/test');
  return DioException(
    requestOptions: opts,
    response: statusCode != null
        ? Response(
            data: data,
            statusCode: statusCode,
            requestOptions: opts,
          )
        : null,
  );
}

void main() {
  group('DioClient.parseError', () {
    test('extrae campo detail del body', () {
      final e = _makeError(
        statusCode: 400,
        data: {'detail': 'El teléfono ya existe'},
      );
      expect(DioClient.parseError(e), equals('El teléfono ya existe'));
    });

    test('extrae campo message del body cuando no hay detail', () {
      final e = _makeError(
        statusCode: 400,
        data: {'message': 'Usuario no encontrado'},
      );
      expect(DioClient.parseError(e), equals('Usuario no encontrado'));
    });

    test('retorna mensaje genérico 400 cuando body no tiene detail/message', () {
      final e = _makeError(statusCode: 400, data: {});
      expect(DioClient.parseError(e), equals('Datos inválidos'));
    });

    test('retorna mensaje genérico 401', () {
      final e = _makeError(statusCode: 401);
      expect(DioClient.parseError(e), equals('Credenciales incorrectas'));
    });

    test('retorna mensaje genérico 403', () {
      final e = _makeError(statusCode: 403);
      expect(DioClient.parseError(e), equals('No tienes permiso para esto'));
    });

    test('retorna mensaje genérico 404', () {
      final e = _makeError(statusCode: 404);
      expect(DioClient.parseError(e), equals('No encontrado'));
    });

    test('retorna mensaje genérico 409', () {
      final e = _makeError(statusCode: 409);
      expect(DioClient.parseError(e), equals('Conflicto con el estado actual'));
    });

    test('retorna mensaje genérico 429', () {
      final e = _makeError(statusCode: 429);
      expect(DioClient.parseError(e),
          equals('Demasiados intentos. Espera unos minutos.'));
    });

    test('retorna mensaje genérico 500', () {
      final e = _makeError(statusCode: 500);
      expect(DioClient.parseError(e),
          equals('Error del servidor. Intenta más tarde.'));
    });

    test('retorna sin conexión para statusCode null (sin respuesta)', () {
      final e = _makeError(statusCode: null);
      expect(DioClient.parseError(e), equals('Sin conexión a internet'));
    });

    test('detail tiene prioridad sobre message', () {
      final e = _makeError(
        statusCode: 400,
        data: {
          'detail': 'Error desde detail',
          'message': 'Error desde message',
        },
      );
      expect(DioClient.parseError(e), equals('Error desde detail'));
    });
  });
}
