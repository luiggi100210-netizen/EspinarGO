import 'package:google_maps_flutter/google_maps_flutter.dart';

import '../../../../core/network/dio_client.dart';
import 'location_service.dart';
import '../../../../core/utils/logger.dart';
import '../models/place_model.dart';
import '../models/route_model.dart';

/// Servicio para buscar lugares y calcular rutas usando Google Maps APIs.
/// Es el único archivo que llama a las APIs de Google Maps.
class MapsService {
  final DioClient _dioClient;

  // URL base de Google APIs
  static const String _baseUrl = 'https://maps.googleapis.com/maps/api';

  // API Key - inyectada en tiempo de compilación con --dart-define.
  // Nunca debe tener un valor por defecto: el repo es público.
  // Ver flutter/README.md para las instrucciones de build.
  static const String _apiKey = String.fromEnvironment('GOOGLE_MAPS_API_KEY');

  MapsService({required DioClient dioClient}) : _dioClient = dioClient;

  /// Busca lugares en Google Geocoding API.
  Future<List<PlaceModel>> searchPlaces(
    String query, {
    LatLng? userLocation,
  }) async {
    if (query.length < 3) return [];

    try {
      final params = <String, dynamic>{
        'address': query,
        'key': _apiKey,
        'language': 'es',
        'region': 'PE',
        'components': 'country:PE',
      };

      if (userLocation != null) {
        params['location'] = '${userLocation.latitude},${userLocation.longitude}';
        params['radius'] = '5000';
      }

      final response = await _dioClient.get(
        '$_baseUrl/geocode/json',
        queryParameters: params,
      );

      final results = response.data['results'] as List<dynamic>? ?? [];
      final places = results
          .map((r) => PlaceModel.fromJson(r as Map<String, dynamic>))
          .toList();

      // Calcular distancia si hay ubicación del usuario
      if (userLocation != null && places.isNotEmpty) {
        for (var i = 0; i < places.length; i++) {
          final place = places[i];
          final distance = LocationService.calculateDistance(
            userLocation,
            LatLng(place.lat, place.lng),
          );
          places[i] = place.copyWith(distanceKm: distance);
        }
        places.sort((a, b) => (a.distanceKm ?? 0).compareTo(b.distanceKm ?? 0));
      }

      return places.take(5).toList();
    } catch (e) {
      AppLogger.error('Error searching places', error: e);
      return [];
    }
  }

  /// Obtiene detalles de un lugar específico.
  Future<PlaceModel?> getPlaceDetails(String placeId) async {
    try {
      final response = await _dioClient.get(
        '$_baseUrl/place/details/json',
        queryParameters: {
          'place_id': placeId,
          'key': _apiKey,
          'language': 'es',
        },
      );

      final result = response.data['result'] as Map<String, dynamic>?;
      if (result != null) {
        return PlaceModel.fromJson(result);
      }
      return null;
    } catch (e) {
      AppLogger.error('Error getting place details', error: e);
      return null;
    }
  }

  /// Calcula la ruta entre dos puntos.
  Future<RouteModel?> getRoute(LatLng origin, LatLng destination) async {
    try {
      final response = await _dioClient.get(
        '$_baseUrl/directions/json',
        queryParameters: {
          'origin': '${origin.latitude},${origin.longitude}',
          'destination': '${destination.latitude},${destination.longitude}',
          'key': _apiKey,
          'language': 'es',
          'mode': 'driving',
          'avoid': 'tolls',
        },
      );

      final originPlace = PlaceModel(
        placeId: 'origin',
        name: 'Origen',
        address: '',
        lat: origin.latitude,
        lng: origin.longitude,
      );

      final destPlace = PlaceModel(
        placeId: 'destination',
        name: 'Destino',
        address: '',
        lat: destination.latitude,
        lng: destination.longitude,
      );

      return RouteModel.fromDirectionsResponse(
        response.data as Map<String, dynamic>,
        originPlace,
        destPlace,
      );
    } catch (e) {
      AppLogger.error('Error calculating route', error: e);
      return null;
    }
  }

  /// Obtiene la dirección desde coordenadas (reverse geocoding).
  Future<PlaceModel?> reverseGeocode(LatLng position) async {
    try {
      final response = await _dioClient.get(
        '$_baseUrl/geocode/json',
        queryParameters: {
          'latlng': '${position.latitude},${position.longitude}',
          'key': _apiKey,
          'language': 'es',
        },
      );

      final results = response.data['results'] as List<dynamic>?;
      if (results != null && results.isNotEmpty) {
        return PlaceModel.fromJson(results.first as Map<String, dynamic>);
      }
      return null;
    } catch (e) {
      AppLogger.error('Error reverse geocoding', error: e);
      return null;
    }
  }
}