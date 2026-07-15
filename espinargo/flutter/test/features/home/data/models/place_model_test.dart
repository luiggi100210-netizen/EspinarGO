import 'package:flutter_test/flutter_test.dart';

import 'package:espinargo_app/features/home/data/models/place_model.dart';

void main() {
  // ── Fixtures ────────────────────────────────────────────────────────────────

  Map<String, dynamic> _fullJson() => {
        'place_id': 'ChIJabc123',
        'formatted_address': 'Plaza de Armas, Espinar, Cusco, Peru',
        'geometry': {
          'location': {'lat': -14.832, 'lng': -71.013},
        },
      };

  PlaceModel _place({
    String id = 'p-1',
    String name = 'Plaza',
    String address = 'Plaza, Espinar',
    double lat = -14.832,
    double lng = -71.013,
  }) =>
      PlaceModel(
        placeId: id,
        name: name,
        address: address,
        lat: lat,
        lng: lng,
      );

  // ── fromJson ───────────────────────────────────────────────────────────────

  group('PlaceModel.fromJson', () {
    test('parsea todos los campos correctamente', () {
      final model = PlaceModel.fromJson(_fullJson());

      expect(model.placeId, equals('ChIJabc123'));
      expect(model.address, equals('Plaza de Armas, Espinar, Cusco, Peru'));
      expect(model.name, equals('Plaza de Armas')); // primera parte antes de coma
      expect(model.lat, closeTo(-14.832, 0.0001));
      expect(model.lng, closeTo(-71.013, 0.0001));
    });

    test('sin geometry → lat y lng son 0.0', () {
      final json = {
        'place_id': 'abc',
        'formatted_address': 'Lugar desconocido',
      };
      final model = PlaceModel.fromJson(json);

      expect(model.lat, equals(0.0));
      expect(model.lng, equals(0.0));
    });

    test('place_id ausente → cadena vacía', () {
      final json = Map<String, dynamic>.from(_fullJson())..remove('place_id');
      final model = PlaceModel.fromJson(json);
      expect(model.placeId, equals(''));
    });

    test('formatted_address sin comas → name igual a address completo', () {
      final json = {
        'place_id': 'abc',
        'formatted_address': 'Espinar',
        'geometry': {
          'location': {'lat': -14.832, 'lng': -71.013},
        },
      };
      final model = PlaceModel.fromJson(json);
      expect(model.name, equals('Espinar'));
      expect(model.address, equals('Espinar'));
    });

    test('distanceKm es null en fromJson (no viene del JSON)', () {
      final model = PlaceModel.fromJson(_fullJson());
      expect(model.distanceKm, isNull);
    });
  });

  // ── toLatLng ───────────────────────────────────────────────────────────────

  group('toLatLng', () {
    test('retorna LatLng con lat y lng correctos', () {
      final model = _place(lat: -14.832, lng: -71.013);
      final latLng = model.toLatLng();

      expect(latLng.latitude, closeTo(-14.832, 0.0001));
      expect(latLng.longitude, closeTo(-71.013, 0.0001));
    });
  });

  // ── shortAddress ───────────────────────────────────────────────────────────

  group('shortAddress', () {
    test('address con comas → retorna primera parte', () {
      final model = _place(address: 'Jr. Junín 123, Espinar, Cusco');
      expect(model.shortAddress, equals('Jr. Junín 123'));
    });

    test('address sin comas → retorna address completo', () {
      final model = _place(address: 'Espinar');
      expect(model.shortAddress, equals('Espinar'));
    });
  });

  // ── formattedDistance ──────────────────────────────────────────────────────

  group('formattedDistance', () {
    test('sin distancia → cadena vacía', () {
      final model = _place();
      expect(model.formattedDistance, equals(''));
    });

    test('distancia < 1 km → formato en metros', () {
      final model = _place().copyWith(distanceKm: 0.5);
      expect(model.formattedDistance, equals('500 m'));
    });

    test('distancia >= 1 km → formato en km', () {
      final model = _place().copyWith(distanceKm: 1.5);
      expect(model.formattedDistance, equals('1.5 km'));
    });
  });

  // ── copyWith ───────────────────────────────────────────────────────────────

  group('copyWith', () {
    test('actualiza distanceKm, preserva el resto', () {
      final original = _place();
      final copy = original.copyWith(distanceKm: 2.3);

      expect(copy.distanceKm, closeTo(2.3, 0.001));
      expect(copy.placeId, equals(original.placeId));
      expect(copy.name, equals(original.name));
      expect(copy.lat, equals(original.lat));
    });
  });
}
