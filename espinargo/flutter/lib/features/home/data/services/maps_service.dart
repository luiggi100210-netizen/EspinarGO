import 'package:google_maps_flutter/google_maps_flutter.dart';

import '../../../../core/network/dio_client.dart';
import '../../../../core/utils/logger.dart';
import '../models/place_model.dart';
import '../models/route_model.dart';

/// Servicio para buscar lugares y calcular rutas usando Google Maps APIs.
/// Es el único archivo que llama a las APIs de Google Maps.
class MapsService {
  final DioClient _dioClient;

  // URL base de Google APIs
  static const String _baseUrl = 'https://maps.googleapis.com/maps/api';

  // API Key - configurada externamente en AndroidManifest.xml
  // y en las variables de entorno del proyecto
  static const String _apiKey = 'YOUR_GOOGLE_MAPS_API_KEY';

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

/// Servicio de ubicación simple para cálculo de distancias.
class LocationService {
  static double calculateDistance(LatLng origin, LatLng destination) {
    // Haversine formula simplificada
    const double earthRadius = 6371; // km
    final dLat = _toRadians(destination.latitude - origin.latitude);
    final dLng = _toRadians(destination.longitude - origin.longitude);
    final a = _sin(dLat / 2) * _sin(dLat / 2) +
        _cos(_toRadians(origin.latitude)) *
            _cos(_toRadians(destination.latitude)) *
            _sin(dLng / 2) *
            _sin(dLng / 2);
    final c = 2 * _atan2(_sqrt(a), _sqrt(1 - a));
    return (earthRadius * c * 100).round() / 100;
  }

  static double _toRadians(double degrees) => degrees * 3.141592653589793 / 180;
  static double _sin(double x) => _taylorSin(x);
  static double _cos(double x) => _taylorCos(x);
  static double _sqrt(double x) => x > 0 ? _newtonSqrt(x) : 0;
  static double _atan2(double y, double x) => _taylorAtan2(y, x);

  static double _taylorSin(double x) {
    x = x % (2 * 3.141592653589793);
    double result = x;
    double term = x;
    for (int i = 1; i <= 10; i++) {
      term *= -x * x / ((2 * i) * (2 * i + 1));
      result += term;
    }
    return result;
  }

  static double _taylorCos(double x) {
    x = x % (2 * 3.141592653589793);
    double result = 1;
    double term = 1;
    for (int i = 1; i <= 10; i++) {
      term *= -x * x / ((2 * i - 1) * (2 * i));
      result += term;
    }
    return result;
  }

  static double _newtonSqrt(double x) {
    double guess = x / 2;
    for (int i = 0; i < 20; i++) {
      guess = (guess + x / guess) / 2;
    }
    return guess;
  }

  static double _taylorAtan2(double y, double x) {
    if (x > 0) return _taylorAtan(y / x);
    if (x < 0 && y >= 0) return _taylorAtan(y / x) + 3.141592653589793;
    if (x < 0 && y < 0) return _taylorAtan(y / x) - 3.141592653589793;
    if (x == 0 && y > 0) return 3.141592653589793 / 2;
    if (x == 0 && y < 0) return -3.141592653589793 / 2;
    return 0;
  }

  static double _taylorAtan(double x) {
    if (x.abs() > 1) {
      return (x > 0 ? 1 : -1) * (3.141592653589793 / 2 - _taylorAtan(1 / x.abs()));
    }
    double result = x;
    double term = x;
    for (int i = 1; i <= 20; i++) {
      term *= -x * x;
      result += term / (2 * i + 1);
    }
    return result;
  }
}