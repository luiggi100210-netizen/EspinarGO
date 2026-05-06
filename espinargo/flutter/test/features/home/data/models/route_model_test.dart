import 'package:flutter_test/flutter_test.dart';
import 'package:google_maps_flutter/google_maps_flutter.dart';

import 'package:espinargo_app/features/home/data/models/place_model.dart';
import 'package:espinargo_app/features/home/data/models/route_model.dart';

void main() {
  // ── Fixtures ────────────────────────────────────────────────────────────────

  PlaceModel _origin() => const PlaceModel(
        placeId: 'origin-1',
        name: 'Plaza de Armas',
        address: 'Plaza de Armas, Espinar',
        lat: -14.832,
        lng: -71.013,
      );

  PlaceModel _destination() => const PlaceModel(
        placeId: 'dest-1',
        name: 'Mercado Central',
        address: 'Mercado Central, Espinar',
        lat: -14.835,
        lng: -71.010,
      );

  Map<String, dynamic> _directionsJson({
    int distanceMeters = 2000,
    int durationSeconds = 480,
    String polyline = '',
  }) =>
      {
        'routes': [
          {
            'legs': [
              {
                'distance': {'text': '${distanceMeters / 1000} km', 'value': distanceMeters},
                'duration': {'text': '$durationSeconds s', 'value': durationSeconds},
              },
            ],
            'overview_polyline': {'points': polyline},
          },
        ],
      };

  RouteModel _route() => RouteModel(
        origin: _origin(),
        destination: _destination(),
        distanceKm: 2.0,
        durationMinutes: 8,
        polylinePoints: const [LatLng(-14.832, -71.013), LatLng(-14.835, -71.010)],
        suggestedPrice: 5.0,
        minPrice: 3.5,
        maxPrice: 7.5,
      );

  // ── fromDirectionsResponse ─────────────────────────────────────────────────

  group('RouteModel.fromDirectionsResponse', () {
    test('parsea distancia y duración correctamente', () {
      final model = RouteModel.fromDirectionsResponse(
        _directionsJson(distanceMeters: 2000, durationSeconds: 480),
        _origin(),
        _destination(),
      );

      expect(model.distanceKm, closeTo(2.0, 0.001));
      expect(model.durationMinutes, equals(8));
      expect(model.origin.placeId, equals('origin-1'));
      expect(model.destination.placeId, equals('dest-1'));
    });

    test('routes vacío → lanza excepción', () {
      expect(
        () => RouteModel.fromDirectionsResponse(
          {'routes': []},
          _origin(),
          _destination(),
        ),
        throwsException,
      );
    });

    test('routes ausente → lanza excepción', () {
      expect(
        () => RouteModel.fromDirectionsResponse(
          {},
          _origin(),
          _destination(),
        ),
        throwsException,
      );
    });

    test('polyline vacío → lista vacía de puntos', () {
      final model = RouteModel.fromDirectionsResponse(
        _directionsJson(polyline: ''),
        _origin(),
        _destination(),
      );
      expect(model.polylinePoints, isEmpty);
    });

    // ── Precios ──────────────────────────────────────────────────────────────

    test('< 1 km → precio sugerido mínimo 3.0', () {
      final model = RouteModel.fromDirectionsResponse(
        _directionsJson(distanceMeters: 500), // 0.5 km
        _origin(),
        _destination(),
      );
      expect(model.suggestedPrice, equals(3.0));
    });

    test('2 km → precio = 2.5 * 2 = 5.0', () {
      final model = RouteModel.fromDirectionsResponse(
        _directionsJson(distanceMeters: 2000),
        _origin(),
        _destination(),
      );
      expect(model.suggestedPrice, equals(5.0));
      expect(model.minPrice, closeTo(3.5, 0.001)); // 5.0 * 0.7
      expect(model.maxPrice, closeTo(7.5, 0.001)); // 5.0 * 1.5
    });

    test('> 3 km → aplica descuento del 10%', () {
      // 5 km: 2.5 * 5 * 0.9 = 11.25 → round a 0.5 → 11.5
      final model = RouteModel.fromDirectionsResponse(
        _directionsJson(distanceMeters: 5000),
        _origin(),
        _destination(),
      );
      expect(model.suggestedPrice, equals(11.5));
    });
  });

  // ── decodePolyline ─────────────────────────────────────────────────────────

  group('decodePolyline', () {
    test('cadena vacía → lista vacía', () {
      final points = RouteModel.decodePolyline('');
      expect(points, isEmpty);
    });

    test('polyline conocido decodifica correctamente', () {
      // Polyline codificada para el punto (38.5, -120.2): "_p~iF~ps|U"
      final points = RouteModel.decodePolyline('_p~iF~ps|U');
      expect(points, hasLength(1));
      expect(points.first.latitude, closeTo(38.5, 0.001));
      expect(points.first.longitude, closeTo(-120.2, 0.001));
    });

    test('polyline de dos puntos decodifica ambos', () {
      // "_p~iF~ps|U_ulLnnqC" → (38.5, -120.2) y (40.7, -120.95)
      final points = RouteModel.decodePolyline('_p~iF~ps|U_ulLnnqC');
      expect(points, hasLength(2));
    });
  });

  // ── getters formateados ────────────────────────────────────────────────────

  group('formattedDistance', () {
    test('2.0 km → "2.0 km"', () {
      expect(_route().formattedDistance, equals('2.0 km'));
    });

    test('0.5 km → "500 m"', () {
      final r = RouteModel(
        origin: _origin(),
        destination: _destination(),
        distanceKm: 0.5,
        durationMinutes: 5,
        polylinePoints: const [],
        suggestedPrice: 3.0,
        minPrice: 2.1,
        maxPrice: 4.5,
      );
      expect(r.formattedDistance, equals('500 m'));
    });
  });

  group('formattedDuration', () {
    test('8 minutos → "8 min"', () {
      expect(_route().formattedDuration, equals('8 min'));
    });

    test('90 minutos → "1 h 30 min"', () {
      final r = RouteModel(
        origin: _origin(),
        destination: _destination(),
        distanceKm: 10.0,
        durationMinutes: 90,
        polylinePoints: const [],
        suggestedPrice: 20.0,
        minPrice: 14.0,
        maxPrice: 30.0,
      );
      expect(r.formattedDuration, equals('1 h 30 min'));
    });

    test('60 minutos → "1 h"', () {
      final r = RouteModel(
        origin: _origin(),
        destination: _destination(),
        distanceKm: 8.0,
        durationMinutes: 60,
        polylinePoints: const [],
        suggestedPrice: 18.0,
        minPrice: 12.6,
        maxPrice: 27.0,
      );
      expect(r.formattedDuration, equals('1 h'));
    });
  });

  group('suggestedPriceFormatted', () {
    test('5.0 → "S/ 5.00"', () {
      expect(_route().suggestedPriceFormatted, equals('S/ 5.00'));
    });
  });
}
