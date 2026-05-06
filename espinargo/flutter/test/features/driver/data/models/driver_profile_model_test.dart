import 'package:flutter_test/flutter_test.dart';

import 'package:espinargo_app/features/driver/data/models/driver_profile_model.dart';

void main() {
  // ── Fixtures ────────────────────────────────────────────────────────────────

  Map<String, dynamic> _fullJson() => {
        'id': 'dp-1',
        'user_id': 'u-1',
        'vehicle_type': 'mototaxi',
        'vehicle_brand': 'Honda',
        'vehicle_model': 'Wave',
        'vehicle_year': 2022,
        'vehicle_color': 'Rojo',
        'vehicle_plate': 'ABC-123',
        'vehicle_seats': 2,
        'vehicle_photo_url': 'https://cdn.example.com/vehicle.jpg',
        'dni_front_url': 'https://cdn.example.com/dni_front.jpg',
        'dni_back_url': 'https://cdn.example.com/dni_back.jpg',
        'license_url': 'https://cdn.example.com/license.jpg',
        'soat_url': 'https://cdn.example.com/soat.jpg',
        'selfie_url': 'https://cdn.example.com/selfie.jpg',
        'driver_status': 'approved',
        'rejection_reason': null,
        'total_trips': 42,
        'rating': 47,
        'rating_count': 10,
        'is_online': true,
      };

  // ── fromJson ───────────────────────────────────────────────────────────────

  group('DriverProfileModel.fromJson', () {
    test('parsea todos los campos correctamente', () {
      final model = DriverProfileModel.fromJson(_fullJson());

      expect(model.id, equals('dp-1'));
      expect(model.userId, equals('u-1'));
      expect(model.vehicleType, equals('mototaxi'));
      expect(model.vehicleBrand, equals('Honda'));
      expect(model.vehicleModel, equals('Wave'));
      expect(model.vehicleYear, equals(2022));
      expect(model.vehicleColor, equals('Rojo'));
      expect(model.vehiclePlate, equals('ABC-123'));
      expect(model.vehicleSeats, equals(2));
      expect(model.driverStatus, equals('approved'));
      expect(model.totalTrips, equals(42));
      expect(model.rating, equals(47));
      expect(model.ratingCount, equals(10));
      expect(model.isOnline, isTrue);
    });

    test('campos opcionales nulos se parsean como null', () {
      final json = {
        'id': 'dp-2',
        'user_id': 'u-2',
        'driver_status': 'pending_docs',
        'vehicle_type': null,
        'vehicle_brand': null,
        'vehicle_model': null,
        'vehicle_year': null,
        'vehicle_color': null,
        'vehicle_plate': null,
        'vehicle_seats': null,
        'vehicle_photo_url': null,
        'dni_front_url': null,
        'dni_back_url': null,
        'license_url': null,
        'soat_url': null,
        'selfie_url': null,
        'rejection_reason': null,
        'total_trips': 0,
        'rating': 0,
        'rating_count': 0,
        'is_online': false,
      };
      final model = DriverProfileModel.fromJson(json);

      expect(model.vehicleType, isNull);
      expect(model.vehicleBrand, isNull);
      expect(model.vehiclePlate, isNull);
    });

    test('driver_status ausente → pending_docs por defecto', () {
      final json = Map<String, dynamic>.from(_fullJson())..remove('driver_status');
      final model = DriverProfileModel.fromJson(json);
      expect(model.driverStatus, equals('pending_docs'));
    });

    test('is_online ausente → false por defecto', () {
      final json = Map<String, dynamic>.from(_fullJson())..remove('is_online');
      final model = DriverProfileModel.fromJson(json);
      expect(model.isOnline, isFalse);
    });

    test('rating y rating_count ausentes → 0 por defecto', () {
      final json = Map<String, dynamic>.from(_fullJson())
        ..remove('rating')
        ..remove('rating_count')
        ..remove('total_trips');
      final model = DriverProfileModel.fromJson(json);
      expect(model.rating, equals(0));
      expect(model.ratingCount, equals(0));
      expect(model.totalTrips, equals(0));
    });
  });

  // ── computed getters ───────────────────────────────────────────────────────

  group('status getters', () {
    test('approved → isApproved = true, canWork = true', () {
      final model = DriverProfileModel.fromJson(_fullJson());
      expect(model.isApproved, isTrue);
      expect(model.canWork, isTrue);
      expect(model.isPendingDocs, isFalse);
      expect(model.isUnderReview, isFalse);
      expect(model.isRejected, isFalse);
    });

    test('pending_docs → isPendingDocs = true', () {
      final model = DriverProfileModel.fromJson({..._fullJson(), 'driver_status': 'pending_docs'});
      expect(model.isPendingDocs, isTrue);
      expect(model.canWork, isFalse);
    });

    test('under_review → isUnderReview = true', () {
      final model = DriverProfileModel.fromJson({..._fullJson(), 'driver_status': 'under_review'});
      expect(model.isUnderReview, isTrue);
      expect(model.canWork, isFalse);
    });

    test('rejected → isRejected = true', () {
      final model = DriverProfileModel.fromJson({..._fullJson(), 'driver_status': 'rejected'});
      expect(model.isRejected, isTrue);
      expect(model.canWork, isFalse);
    });
  });

  group('ratingDisplay', () {
    test('rating 47 → ratingDisplay 4.7', () {
      final model = DriverProfileModel.fromJson(_fullJson());
      expect(model.ratingDisplay, closeTo(4.7, 0.001));
    });

    test('rating 0 → ratingDisplay 0.0', () {
      final model = DriverProfileModel.fromJson({..._fullJson(), 'rating': 0});
      expect(model.ratingDisplay, equals(0.0));
    });

    test('rating 50 → ratingDisplay 5.0 (máximo)', () {
      final model = DriverProfileModel.fromJson({..._fullJson(), 'rating': 50});
      expect(model.ratingDisplay, equals(5.0));
    });
  });

  group('vehicleDescription', () {
    test('brand y model presentes → "Honda Wave"', () {
      final model = DriverProfileModel.fromJson(_fullJson());
      expect(model.vehicleDescription, equals('Honda Wave'));
    });

    test('solo brand → muestra solo brand', () {
      final model = DriverProfileModel.fromJson(
          {..._fullJson(), 'vehicle_model': null});
      expect(model.vehicleDescription, equals('Honda'));
    });

    test('solo model → muestra solo model', () {
      final model = DriverProfileModel.fromJson(
          {..._fullJson(), 'vehicle_brand': null});
      expect(model.vehicleDescription, equals('Wave'));
    });

    test('sin brand ni model → texto por defecto', () {
      final model = DriverProfileModel.fromJson(
          {..._fullJson(), 'vehicle_brand': null, 'vehicle_model': null});
      expect(model.vehicleDescription, equals('Vehículo sin registrar'));
    });
  });

  // ── copyWith ───────────────────────────────────────────────────────────────

  group('copyWith', () {
    test('actualiza solo los campos indicados', () {
      final original = DriverProfileModel.fromJson(_fullJson());
      final copy = original.copyWith(
        driverStatus: 'under_review',
        isOnline: false,
      );

      expect(copy.driverStatus, equals('under_review'));
      expect(copy.isOnline, isFalse);
      expect(copy.id, equals(original.id));
      expect(copy.vehicleBrand, equals(original.vehicleBrand));
    });
  });
}
