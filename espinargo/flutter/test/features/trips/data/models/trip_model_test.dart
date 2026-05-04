import 'package:flutter_test/flutter_test.dart';
import 'package:intl/date_symbol_data_local.dart';
import 'package:espinargo_app/features/trips/data/models/trip_model.dart';

Map<String, dynamic> _tripJson({String status = 'searching'}) => {
      'id': 'trip-1',
      'passenger': null,
      'driver': null,
      'origin_address': 'Av. Principal 123',
      'origin_lat': '-14.7953',
      'origin_lng': '-71.4138',
      'dest_address': 'Plaza de Armas',
      'dest_lat': '-14.7900',
      'dest_lng': '-71.4100',
      'proposed_price': '10.00',
      'final_price': null,
      'status': status,
      'payment_method': 'cash',
      'distance_km': null,
      'duration_minutes': null,
      'cancel_reason': null,
      'created_at': '2024-01-20T10:00:00Z',
    };

void main() {
  setUpAll(() async {
    await initializeDateFormatting('es');
  });

  group('TripModel.fromJson', () {
    test('parsea campos básicos correctamente', () {
      final trip = TripModel.fromJson(_tripJson());
      expect(trip.id, equals('trip-1'));
      expect(trip.originAddress, equals('Av. Principal 123'));
      expect(trip.destAddress, equals('Plaza de Armas'));
      expect(trip.proposedPrice, equals('10.00'));
      expect(trip.status, equals('searching'));
      expect(trip.paymentMethod, equals('cash'));
      expect(trip.finalPrice, isNull);
      expect(trip.passenger, isNull);
      expect(trip.driver, isNull);
    });

    test('usa valores por defecto cuando faltan campos', () {
      final trip = TripModel.fromJson({'id': 'trip-2', 'created_at': '2024-01-01'});
      expect(trip.originAddress, equals(''));
      expect(trip.proposedPrice, equals('0'));
      expect(trip.status, equals('searching'));
      expect(trip.paymentMethod, equals('cash'));
    });
  });

  group('TripModel.toJson', () {
    test('serializa todos los campos', () {
      final trip = TripModel.fromJson(_tripJson());
      final json = trip.toJson();
      expect(json['id'], equals('trip-1'));
      expect(json['origin_address'], equals('Av. Principal 123'));
      expect(json['status'], equals('searching'));
    });
  });

  group('TripModel getters de estado', () {
    final activeStatuses = ['searching', 'negotiating', 'accepted', 'in_progress'];
    for (final status in activeStatuses) {
      test('isActive es true para status "$status"', () {
        final trip = TripModel.fromJson(_tripJson(status: status));
        expect(trip.isActive, isTrue);
      });
    }

    test('isActive es false para status "completed"', () {
      expect(TripModel.fromJson(_tripJson(status: 'completed')).isActive, isFalse);
    });

    test('isActive es false para status "cancelled"', () {
      expect(TripModel.fromJson(_tripJson(status: 'cancelled')).isActive, isFalse);
    });

    test('isCompleted es true para status "completed"', () {
      expect(
          TripModel.fromJson(_tripJson(status: 'completed')).isCompleted, isTrue);
    });

    test('isCancelled es true para status "cancelled"', () {
      expect(
          TripModel.fromJson(_tripJson(status: 'cancelled')).isCancelled, isTrue);
    });

    test('hasDriver es false cuando driver es null', () {
      expect(TripModel.fromJson(_tripJson()).hasDriver, isFalse);
    });
  });

  group('TripModel.displayPrice', () {
    test('muestra precio propuesto cuando no hay precio final', () {
      final trip = TripModel.fromJson(_tripJson());
      expect(trip.displayPrice, contains('10.00'));
    });

    test('muestra precio final cuando existe', () {
      final trip = TripModel.fromJson({
        ..._tripJson(),
        'proposed_price': '10.00',
        'final_price': '12.00',
      });
      expect(trip.displayPrice, contains('12.00'));
    });
  });

  group('TripModel.originLatLng / destLatLng', () {
    test('convierte coordenadas correctamente', () {
      final trip = TripModel.fromJson(_tripJson());
      expect(trip.originLatLng.latitude, closeTo(-14.7953, 0.0001));
      expect(trip.originLatLng.longitude, closeTo(-71.4138, 0.0001));
      expect(trip.destLatLng.latitude, closeTo(-14.79, 0.0001));
    });

    test('retorna 0,0 para coordenadas inválidas', () {
      final trip = TripModel.fromJson({
        ..._tripJson(),
        'origin_lat': 'invalid',
        'origin_lng': 'invalid',
      });
      expect(trip.originLatLng.latitude, equals(0));
      expect(trip.originLatLng.longitude, equals(0));
    });
  });

  group('TripModel.copyWith', () {
    test('actualiza solo el campo indicado', () {
      final trip = TripModel.fromJson(_tripJson());
      final updated = trip.copyWith(status: 'accepted');
      expect(updated.status, equals('accepted'));
      expect(updated.id, equals(trip.id));
      expect(updated.originAddress, equals(trip.originAddress));
    });
  });
}
