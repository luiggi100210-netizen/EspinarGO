import 'package:flutter_test/flutter_test.dart';
import 'package:intl/date_symbol_data_local.dart';
import 'package:espinargo_app/features/trips/data/models/trip_offer_model.dart';

final _driverJson = {
  'id': 'd-1',
  'full_name': 'Carlos Mamani',
  'phone_number': '+51976543210',
  'role': 'driver',
  'status': 'active',
  'phone_verified': true,
  'preferred_lang': 'es',
  'created_at': '2024-01-01T00:00:00Z',
};

Map<String, dynamic> _offerJson({
  String offeredPrice = '8.00',
  String? expiresAt,
  bool isAccepted = false,
  Map<String, dynamic>? driverProfile,
}) =>
    {
      'id': 'offer-1',
      'trip_id': 'trip-1',
      'driver': _driverJson,
      'driver_profile': driverProfile,
      'offered_price': offeredPrice,
      'message': 'Voy en 2 minutos',
      'is_accepted': isAccepted,
      'expires_at':
          expiresAt ?? DateTime.now().add(const Duration(minutes: 2)).toIso8601String(),
      'created_at': '2024-01-20T10:00:00Z',
    };

void main() {
  setUpAll(() async {
    await initializeDateFormatting('es');
  });

  group('TripOfferModel.fromJson', () {
    test('parsea todos los campos correctamente', () {
      final offer = TripOfferModel.fromJson(_offerJson());
      expect(offer.id, equals('offer-1'));
      expect(offer.tripId, equals('trip-1'));
      expect(offer.offeredPrice, equals('8.00'));
      expect(offer.message, equals('Voy en 2 minutos'));
      expect(offer.isAccepted, isFalse);
      expect(offer.driver.fullName, equals('Carlos Mamani'));
    });

    test('isAccepted es false por defecto', () {
      final json = _offerJson()..remove('is_accepted');
      final offer = TripOfferModel.fromJson(json);
      expect(offer.isAccepted, isFalse);
    });
  });

  group('TripOfferModel.toJson', () {
    test('serializa todos los campos', () {
      final offer = TripOfferModel.fromJson(_offerJson());
      final json = offer.toJson();
      expect(json['id'], equals('offer-1'));
      expect(json['offered_price'], equals('8.00'));
      expect(json['message'], equals('Voy en 2 minutos'));
    });
  });

  group('TripOfferModel.isExpired', () {
    test('no expirada cuando expires_at está en el futuro', () {
      final offer = TripOfferModel.fromJson(_offerJson());
      expect(offer.isExpired, isFalse);
    });

    test('expirada cuando expires_at está en el pasado', () {
      final pastDate =
          DateTime.now().subtract(const Duration(minutes: 5)).toIso8601String();
      final offer = TripOfferModel.fromJson(_offerJson(expiresAt: pastDate));
      expect(offer.isExpired, isTrue);
    });

    test('no expirada con fecha inválida (retorna false por defecto)', () {
      final offer = TripOfferModel.fromJson(
          {..._offerJson(), 'expires_at': 'fecha-invalida'});
      expect(offer.isExpired, isFalse);
    });
  });

  group('TripOfferModel.formattedPrice', () {
    test('formatea el precio correctamente', () {
      final offer = TripOfferModel.fromJson(_offerJson(offeredPrice: '8.00'));
      expect(offer.formattedPrice, contains('8.00'));
      expect(offer.formattedPrice, contains('S/'));
    });
  });

  group('TripOfferModel driverProfile getters', () {
    test('vehicleType retorna mototaxi por defecto', () {
      final offer = TripOfferModel.fromJson(_offerJson());
      expect(offer.vehicleType, equals('mototaxi'));
    });

    test('vehicleType retorna el valor del perfil cuando existe', () {
      final offer = TripOfferModel.fromJson(
          _offerJson(driverProfile: {'vehicle_type': 'car'}));
      expect(offer.vehicleType, equals('car'));
    });

    test('driverRating retorna 5.0 por defecto', () {
      final offer = TripOfferModel.fromJson(_offerJson());
      expect(offer.driverRating, equals(5.0));
    });

    test('driverRating convierte int a double', () {
      final offer = TripOfferModel.fromJson(
          _offerJson(driverProfile: {'rating_display': 4}));
      expect(offer.driverRating, equals(4.0));
    });

    test('driverTrips retorna 0 por defecto', () {
      final offer = TripOfferModel.fromJson(_offerJson());
      expect(offer.driverTrips, equals(0));
    });
  });

  group('TripOfferModel.timeUntilExpiry', () {
    test('retorna "0:00" para oferta ya expirada', () {
      final past =
          DateTime.now().subtract(const Duration(minutes: 1)).toIso8601String();
      final offer = TripOfferModel.fromJson(_offerJson(expiresAt: past));
      expect(offer.timeUntilExpiry, equals('0:00'));
    });

    test('retorna formato m:ss para oferta vigente', () {
      final future =
          DateTime.now().add(const Duration(minutes: 2)).toIso8601String();
      final offer = TripOfferModel.fromJson(_offerJson(expiresAt: future));
      // El resultado debe contener ":" y ser m:ss
      expect(offer.timeUntilExpiry, contains(':'));
    });
  });

  group('TripOfferModel.copyWith', () {
    test('actualiza solo el campo indicado', () {
      final offer = TripOfferModel.fromJson(_offerJson());
      final updated = offer.copyWith(isAccepted: true);
      expect(updated.isAccepted, isTrue);
      expect(updated.id, equals(offer.id));
      expect(updated.offeredPrice, equals(offer.offeredPrice));
    });
  });
}
