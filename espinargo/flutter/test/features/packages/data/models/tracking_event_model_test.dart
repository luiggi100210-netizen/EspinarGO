import 'package:flutter_test/flutter_test.dart';

import 'package:espinargo_app/features/packages/data/models/tracking_event_model.dart';

void main() {
  group('TrackingEventModel.fromJson', () {
    test('parsea todos los campos correctamente', () {
      final json = {
        'id': 'evt-1',
        'status': 'pending',
        'description': 'Paquete registrado en el sistema',
        'created_at': '2024-01-01T10:00:00Z',
        'location_lat': '-14.832',
        'location_lng': '-71.013',
        'updated_by': 'sistema',
      };

      final model = TrackingEventModel.fromJson(json);

      expect(model.id, equals('evt-1'));
      expect(model.status, equals('pending'));
      expect(model.description, equals('Paquete registrado en el sistema'));
      expect(model.createdAt, equals('2024-01-01T10:00:00Z'));
      expect(model.locationLat, equals('-14.832'));
      expect(model.locationLng, equals('-71.013'));
      expect(model.updatedBy, equals('sistema'));
    });

    test('campos opcionales nulos se parsean como null', () {
      final json = {
        'id': 'evt-2',
        'status': 'in_transit',
        'description': 'En camino',
        'created_at': '2024-01-02T00:00:00Z',
        'location_lat': null,
        'location_lng': null,
        'updated_by': null,
      };

      final model = TrackingEventModel.fromJson(json);

      expect(model.locationLat, isNull);
      expect(model.locationLng, isNull);
      expect(model.updatedBy, isNull);
    });

    test('description ausente → cadena vacía', () {
      final json = {
        'id': 'evt-3',
        'status': 'assigned',
        'created_at': '2024-01-03T00:00:00Z',
      };

      final model = TrackingEventModel.fromJson(json);

      expect(model.description, equals(''));
    });

    test('status delivered → statusLabel no es nulo', () {
      final json = {
        'id': 'evt-4',
        'status': 'delivered',
        'description': 'Entregado',
        'created_at': '2024-01-04T00:00:00Z',
      };

      final model = TrackingEventModel.fromJson(json);

      expect(model.statusLabel, isNotNull);
      expect(model.statusLabel, isNotEmpty);
    });
  });
}
