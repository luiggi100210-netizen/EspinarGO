import 'package:flutter_test/flutter_test.dart';
import 'package:espinargo_app/features/trips/data/models/trip_model.dart';
import 'package:espinargo_app/features/trips/data/models/trip_offer_model.dart';
import 'package:espinargo_app/features/trips/domain/providers/trip_state.dart';

TripModel _makeTrip({String status = 'searching'}) => TripModel(
      id: 'trip-1',
      originAddress: 'Origen',
      originLat: '-14.79',
      originLng: '-71.41',
      destAddress: 'Destino',
      destLat: '-14.80',
      destLng: '-71.42',
      proposedPrice: '10.00',
      status: status,
      paymentMethod: 'cash',
      createdAt: '2024-01-01T00:00:00Z',
    );

TripOfferModel _makeOffer() => TripOfferModel(
      id: 'offer-1',
      tripId: 'trip-1',
      driver: _makeTrip().passenger ??
          (throw Exception('No debería llegar aquí')),
      offeredPrice: '8.00',
      expiresAt: DateTime.now().add(const Duration(minutes: 2)).toIso8601String(),
      createdAt: '2024-01-01T00:00:00Z',
    );

void main() {
  group('TripState factories', () {
    test('estado por defecto — idle, sin viaje, sin ofertas', () {
      const state = TripState();
      expect(state.flowStatus, equals(TripFlowStatus.idle));
      expect(state.currentTrip, isNull);
      expect(state.offers, isEmpty);
      expect(state.isLoading, isFalse);
      expect(state.errorMessage, isNull);
    });

    test('loading — isLoading true', () {
      final state = TripState.loading();
      expect(state.isLoading, isTrue);
    });

    test('searching — tiene viaje y estado searching', () {
      final trip = _makeTrip();
      final state = TripState.searching(trip);
      expect(state.flowStatus, equals(TripFlowStatus.searching));
      expect(state.currentTrip, equals(trip));
      expect(state.isLoading, isFalse);
    });

    test('hasOffers — tiene viaje y lista de ofertas', () {
      final trip = _makeTrip();
      final state = TripState.hasOffers(trip, []);
      expect(state.flowStatus, equals(TripFlowStatus.hasOffers));
      expect(state.currentTrip, equals(trip));
    });

    test('error — estado error con mensaje', () {
      final state = TripState.error('Sin conductores');
      expect(state.flowStatus, equals(TripFlowStatus.error));
      expect(state.errorMessage, equals('Sin conductores'));
    });
  });

  group('TripState getters', () {
    test('hasActiveTrip es false sin viaje', () {
      expect(const TripState().hasActiveTrip, isFalse);
    });

    test('hasActiveTrip es true con viaje activo', () {
      final state = TripState.searching(_makeTrip(status: 'searching'));
      expect(state.hasActiveTrip, isTrue);
    });

    test('hasActiveTrip es false con viaje completado', () {
      final state = TripState.searching(_makeTrip(status: 'completed'));
      expect(state.hasActiveTrip, isFalse);
    });

    test('canAcceptOffers es true solo en estado hasOffers', () {
      expect(
          TripState.hasOffers(_makeTrip(), []).canAcceptOffers, isTrue);
      expect(
          TripState.searching(_makeTrip()).canAcceptOffers, isFalse);
      expect(const TripState().canAcceptOffers, isFalse);
    });

    test('offersCount retorna cantidad de ofertas', () {
      const state = TripState(offers: []);
      expect(state.offersCount, equals(0));
    });
  });

  group('TripState.statusMessage', () {
    test('idle — mensaje de bienvenida', () {
      expect(const TripState().statusMessage, equals('¿A dónde vas hoy?'));
    });

    test('searching — buscando conductores', () {
      expect(
          TripState.searching(_makeTrip()).statusMessage,
          contains('Buscando'));
    });

    test('completed — llegaste a destino', () {
      const state = TripState(flowStatus: TripFlowStatus.completed);
      expect(state.statusMessage, contains('destino'));
    });

    test('error — muestra el mensaje de error', () {
      final state = TripState.error('Timeout de búsqueda');
      expect(state.statusMessage, equals('Timeout de búsqueda'));
    });

    test('cancelled — viaje cancelado', () {
      const state = TripState(flowStatus: TripFlowStatus.cancelled);
      expect(state.statusMessage, equals('Viaje cancelado'));
    });
  });

  group('TripState.copyWith', () {
    test('actualiza solo los campos indicados', () {
      const state = TripState(flowStatus: TripFlowStatus.searching);
      final updated = state.copyWith(
        flowStatus: TripFlowStatus.hasOffers,
        isLoading: true,
      );
      expect(updated.flowStatus, equals(TripFlowStatus.hasOffers));
      expect(updated.isLoading, isTrue);
      expect(updated.currentTrip, isNull);
    });

    test('errorMessage se puede limpiar pasando null', () {
      const state = TripState(errorMessage: 'Error previo');
      final cleared = state.copyWith(errorMessage: null);
      expect(cleared.errorMessage, isNull);
    });

    test('preserva la lista de ofertas existente', () {
      const state = TripState(offers: []);
      final updated = state.copyWith(isLoading: false);
      expect(updated.offers, isEmpty);
    });
  });
}
