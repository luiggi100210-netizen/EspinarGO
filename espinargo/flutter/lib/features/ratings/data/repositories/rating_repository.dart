import 'package:dio/dio.dart';

import '../../../../core/constants/api_constants.dart';
import '../../../../core/network/dio_client.dart';
import '../models/rating_model.dart';

/// Repositorio de calificaciones.
class RatingRepository {
  final DioClient _dioClient;

  RatingRepository({required DioClient dioClient}) : _dioClient = dioClient;

  /// Envía la calificación de un viaje completado.
  Future<RatingModel> createRating({
    required String tripId,
    required int score,
    String? comment,
  }) async {
    try {
      final response = await _dioClient.post(
        ApiConstants.RATINGS,
        data: {
          'trip_id': tripId,
          'score': score,
          if (comment != null && comment.isNotEmpty) 'comment': comment,
        },
      );
      return RatingModel.fromJson(response.data as Map<String, dynamic>);
    } on DioException catch (e) {
      throw Exception(_handleError(e));
    }
  }

  /// Obtiene las calificaciones recibidas por el usuario autenticado.
  Future<List<RatingModel>> getReceivedRatings({int page = 1, int perPage = 20}) async {
    try {
      final response = await _dioClient.get(
        '${ApiConstants.RATINGS}/received',
        queryParameters: {'page': page, 'per_page': perPage},
      );
      final data = response.data as List<dynamic>;
      return data.map((e) => RatingModel.fromJson(e as Map<String, dynamic>)).toList();
    } on DioException catch (e) {
      throw Exception(_handleError(e));
    }
  }

  String _handleError(DioException e) {
    if (e.response?.data != null && e.response?.data is Map) {
      final detail = (e.response!.data as Map<String, dynamic>)['detail'];
      if (detail != null) return detail as String;
    }
    switch (e.response?.statusCode) {
      case 400:
        return 'No se pudo enviar la calificación';
      case 403:
        return 'No participaste en este viaje';
      case 404:
        return 'Viaje no encontrado';
      default:
        return 'Sin conexión';
    }
  }
}
