import 'package:dio/dio.dart';

import '../../../../core/constants/api_constants.dart';
import '../../../../core/network/dio_client.dart';
import '../models/trip_model.dart';
import '../models/trip_offer_model.dart';

/// Repositorio que maneja todas las llamadas a la API de viajes.
class TripRepository {
  final DioClient _dioClient;

  TripRepository({required DioClient dioClient}) : _dioClient = dioClient;

  /// Crea un nuevo viaje.
  Future<TripModel> createTrip({
    required String originAddress,
    required double originLat,
    required double originLng,
    required String destAddress,
    required double destLat,
    required double destLng,
    required String proposedPrice,
    String paymentMethod = 'cash',
  }) async {
    try {
      final response = await _dioClient.post(
        ApiConstants.TRIPS,
        data: {
          'origin_address': originAddress,
          'origin_lat': originLat,
          'origin_lng': originLng,
          'dest_address': destAddress,
          'dest_lat': destLat,
          'dest_lng': destLng,
          'proposed_price': proposedPrice,
          'payment_method': paymentMethod,
        },
      );
      return TripModel.fromJson(response.data as Map<String, dynamic>);
    } on DioException catch (e) {
      throw Exception(DioClient.parseError(e));
    }
  }

  /// Obtiene el viaje activo del usuario.
  Future<TripModel?> getActiveTrip() async {
    try {
      final response = await _dioClient.get('${ApiConstants.TRIPS}/active');
      return TripModel.fromJson(response.data as Map<String, dynamic>);
    } on DioException catch (e) {
      if (e.response?.statusCode == 404) {
        return null;
      }
      throw Exception(DioClient.parseError(e));
    }
  }

  /// Obtiene las ofertas de un viaje.
  Future<List<TripOfferModel>> getTripOffers(String tripId) async {
    try {
      final response = await _dioClient.get(
        ApiConstants.tripOffers(tripId),
      );
      final data = response.data as List<dynamic>;
      return data
          .map((json) => TripOfferModel.fromJson(json as Map<String, dynamic>))
          .toList();
    } on DioException catch (e) {
      throw Exception(DioClient.parseError(e));
    }
  }

  /// Acepta una oferta.
  Future<TripModel> acceptOffer({
    required String tripId,
    required String offerId,
  }) async {
    try {
      final response = await _dioClient.post(
        ApiConstants.acceptOffer(tripId),
        data: {'offer_id': offerId},
      );
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
        data: {'cancel_reason': 'passenger_cancel'},
      );
      return TripModel.fromJson(response.data as Map<String, dynamic>);
    } on DioException catch (e) {
      throw Exception(DioClient.parseError(e));
    }
  }

  /// Obtiene el historial de viajes.
  Future<List<TripModel>> getTripHistory({
    int page = 1,
    int perPage = 20,
  }) async {
    try {
      final response = await _dioClient.get(
        '${ApiConstants.TRIPS}/history',
        queryParameters: {'page': page, 'per_page': perPage},
      );
      final data = response.data as List<dynamic>;
      return data
          .map((json) => TripModel.fromJson(json as Map<String, dynamic>))
          .toList();
    } on DioException catch (e) {
      throw Exception(DioClient.parseError(e));
    }
  }

  /// Obtiene un viaje por ID.
  Future<TripModel> getTripById(String tripId) async {
    try {
      final response = await _dioClient.get(ApiConstants.tripById(tripId));
      return TripModel.fromJson(response.data as Map<String, dynamic>);
    } on DioException catch (e) {
      throw Exception(DioClient.parseError(e));
    }
  }

}