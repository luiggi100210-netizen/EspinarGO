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
      final response = await _dioClient.get(ApiConstants.MY_DRIVER_PROFILE);
      return DriverProfileModel.fromJson(response.data as Map<String, dynamic>);
    } on DioException catch (e) {
      throw Exception(DioClient.parseError(e));
    }
  }

  /// Activa o desactiva el modo online.
  Future<DriverProfileModel> setOnlineStatus(bool isOnline) async {
    try {
      final response = await _dioClient.patch(
        ApiConstants.DRIVER_ONLINE_STATUS,
        data: {'is_online': isOnline},
      );
      return DriverProfileModel.fromJson(response.data as Map<String, dynamic>);
    } on DioException catch (e) {
      throw Exception(DioClient.parseError(e));
    }
  }

  /// Actualiza la ubicación del conductor.
  Future<void> updateDriverLocation({
    required double lat,
    required double lng,
  }) async {
    try {
      await _dioClient.patch(
        ApiConstants.DRIVER_LOCATION,
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
        ApiConstants.makeOffer(tripId),
        data: {
          'offered_price': offeredPrice,
          if (message != null) 'message': message,
        },
      );
      return TripOfferModel.fromJson(response.data as Map<String, dynamic>);
    } on DioException catch (e) {
      throw Exception(DioClient.parseError(e));
    }
  }

  /// Inicia un viaje (conductor confirma que el pasajero está a bordo).
  Future<TripModel> startTrip(String tripId) async {
    try {
      final response = await _dioClient.post(ApiConstants.startTrip(tripId));
      return TripModel.fromJson(response.data as Map<String, dynamic>);
    } on DioException catch (e) {
      throw Exception(DioClient.parseError(e));
    }
  }

  /// Completa un viaje.
  Future<TripModel> completeTrip(String tripId) async {
    try {
      final response = await _dioClient.post(ApiConstants.completeTrip(tripId));
      return TripModel.fromJson(response.data as Map<String, dynamic>);
    } on DioException catch (e) {
      throw Exception(DioClient.parseError(e));
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
      throw Exception(DioClient.parseError(e));
    }
  }

  /// Obtiene el historial de viajes del conductor.
  Future<List<TripModel>> getDriverTripsHistory({
    int page = 1,
    int perPage = 20,
  }) async {
    try {
      final response = await _dioClient.get(
        '${ApiConstants.TRIPS}${ApiConstants.HISTORY}',
        queryParameters: {'page': page, 'per_page': perPage},
      );
      final data = response.data as List<dynamic>;
      return data.map((json) => TripModel.fromJson(json as Map<String, dynamic>)).toList();
    } on DioException catch (e) {
      throw Exception(DioClient.parseError(e));
    }
  }

  /// Obtiene las ganancias del conductor.
  Future<Map<String, dynamic>> getDriverEarnings() async {
    try {
      final response = await _dioClient.get(ApiConstants.DRIVER_EARNINGS);
      return response.data as Map<String, dynamic>;
    } on DioException catch (e) {
      throw Exception(DioClient.parseError(e));
    }
  }
}