import 'package:dio/dio.dart';

import '../../../../core/constants/api_constants.dart';
import '../../../../core/network/dio_client.dart';
import '../../../trips/data/models/trip_model.dart';
import '../../../trips/data/models/trip_offer_model.dart';
import '../models/driver_profile_model.dart';

/// Repositorio de operaciones del conductor.
class DriverRepository {
  final DioClient _dioClient;

  DriverRepository({required DioClient dioClient}) : _dioClient = dioClient;

  /// Obtiene el perfil del conductor.
  Future<DriverProfileModel> getMyDriverProfile() async {
    try {
      final response = await _dioClient.get('/api/v1/users/me/driver-profile');
      return DriverProfileModel.fromJson(response.data as Map<String, dynamic>);
    } on DioException catch (e) {
      throw Exception(_handleError(e));
    }
  }

  /// Activa o desactiva el modo online.
  Future<DriverProfileModel> setOnlineStatus(bool isOnline) async {
    try {
      final response = await _dioClient.patch(
        '/api/v1/users/me/driver-profile/online',
        data: {'is_online': isOnline},
      );
      return DriverProfileModel.fromJson(response.data as Map<String, dynamic>);
    } on DioException catch (e) {
      throw Exception(_handleError(e));
    }
  }

  /// Actualiza la ubicación del conductor.
  Future<void> updateDriverLocation({
    required double lat,
    required double lng,
  }) async {
    try {
      await _dioClient.patch(
        '/api/v1/users/me/driver-profile/location',
        data: {
          'current_lat': lat.toString(),
          'current_lng': lng.toString(),
        },
      );
    } catch (_) {
      // Silencioso: no lanzar excepción si falla
    }
  }

  /// Hace una oferta a un viaje.
  Future<TripOfferModel> makeOffer({
    required String tripId,
    required String offeredPrice,
    String? message,
  }) async {
    try {
      final response = await _dioClient.post(
        '/api/v1/trips/$tripId/offer',
        data: {
          'offered_price': offeredPrice,
          if (message != null) 'message': message,
        },
      );
      return TripOfferModel.fromJson(response.data as Map<String, dynamic>);
    } on DioException catch (e) {
      throw Exception(_handleError(e));
    }
  }

  /// Inicia un viaje (conductor confirma que el pasajero está a bordo).
  Future<TripModel> startTrip(String tripId) async {
    try {
      final response = await _dioClient.post(ApiConstants.startTrip(tripId));
      return TripModel.fromJson(response.data as Map<String, dynamic>);
    } on DioException catch (e) {
      throw Exception(_handleError(e));
    }
  }

  /// Completa un viaje.
  Future<TripModel> completeTrip(String tripId) async {
    try {
      final response = await _dioClient.post(ApiConstants.completeTrip(tripId));
      return TripModel.fromJson(response.data as Map<String, dynamic>);
    } on DioException catch (e) {
      throw Exception(_handleError(e));
    }
  }

  /// Cancela un viaje.
  Future<TripModel> cancelTrip(String tripId) async {
    try {
      final response = await _dioClient.post(
        ApiConstants.cancelTrip(tripId),
        data: {'cancel_reason': 'driver_cancel'},
      );
      return TripModel.fromJson(response.data as Map<String, dynamic>);
    } on DioException catch (e) {
      throw Exception(_handleError(e));
    }
  }

  /// Obtiene el historial de viajes del conductor.
  Future<List<TripModel>> getDriverTripsHistory({
    int page = 1,
    int perPage = 20,
  }) async {
    try {
      final response = await _dioClient.get(
        '/api/v1/trips/history',
        queryParameters: {'page': page, 'per_page': perPage},
      );
      final data = response.data as List<dynamic>;
      return data.map((json) => TripModel.fromJson(json as Map<String, dynamic>)).toList();
    } on DioException catch (e) {
      throw Exception(_handleError(e));
    }
  }

  /// Obtiene las ganancias del conductor.
  Future<Map<String, dynamic>> getDriverEarnings() async {
    try {
      final response = await _dioClient.get('/api/v1/trips/driver/earnings');
      return response.data as Map<String, dynamic>;
    } on DioException catch (e) {
      throw Exception(_handleError(e));
    }
  }

  /// Manejo de errores.
  String _handleError(DioException e) {
    if (e.response?.data != null && e.response?.data is Map) {
      final data = e.response?.data as Map<String, dynamic>;
      if (data['detail'] != null) return data['detail'] as String;
      if (data['message'] != null) return data['message'] as String;
    }
    switch (e.response?.statusCode) {
      case 400:
        return 'Datos inválidos';
      case 403:
        return 'No tienes permiso para esto';
      case 404:
        return 'No encontrado';
      case 500:
        return 'Error del servidor';
      default:
        return 'Sin conexión';
    }
  }
}