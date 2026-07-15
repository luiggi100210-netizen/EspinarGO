import 'dart:async';

import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:mocktail/mocktail.dart';

import 'package:espinargo_app/features/auth/data/models/user_model.dart';
import 'package:espinargo_app/features/trips/data/models/trip_model.dart';
import 'package:espinargo_app/features/trips/data/models/trip_offer_model.dart';
import 'package:espinargo_app/features/trips/data/repositories/trip_repository.dart';
import 'package:espinargo_app/features/trips/data/services/trip_websocket_service.dart';
import 'package:espinargo_app/features/trips/domain/providers/trip_provider.dart';
import 'package:espinargo_app/features/trips/domain/providers/trip_state.dart';

// ── Mocks ─────────────────────────────────────────────────────────────────────

class MockTripRepository extends Mock implements TripRepository {}
class MockTripWebSocketService extends Mock implements TripWebSocketService {}

// ── Fixtures ──────────────────────────────────────────────────────────────────

TripModel _makeTrip({String id = 'trip-1', String status = 'searching'}) => TripModel(
      id: id,
      originAddress: 'Calle A',
      originLat: '-14.79',
      originLng: '-71.41',
      destAddress: 'Calle B',
      destLat: '-14.80',
      destLng: '-71.42',
      proposedPrice: '10.00',
      status: status,
      paymentMethod: 'cash',
      createdAt: '2024-01-01T00:00:00Z',
    );

UserModel _makeDriver() => const UserModel(
      id: 'driver-1',
      fullName: 'Carlos Díaz',
      phoneNumber: '+51976543210',
      role: 'driver',
      status: 'active',
      phoneVerified: true,
      preferredLang: 'es',
      createdAt: '2024-01-01T00:00:00Z',
    );

TripOfferModel _makeOffer({String id = 'offer-1'}) => TripOfferModel(
      id: id,
      tripId: 'trip-1',
      driver: _makeDriver(),
      offeredPrice: '8.00',
      expiresAt: DateTime.now().add(const Duration(minutes: 5)).toIso8601String(),
      createdAt: '2024-01-01T00:00:00Z',
    );

// ── Helper ────────────────────────────────────────────────────────────────────

void _stubIdleWs(MockTripWebSocketService ws) {
  when(() => ws.connect(any())).thenAnswer((_) async {});
  when(() => ws.onNewOffer).thenAnswer((_) => const Stream.empty());
  when(() => ws.onTripUpdated).thenAnswer((_) => const Stream.empty());
  when(() => ws.onDriverLocation).thenAnswer((_) => const Stream.empty());
  when(() => ws.onTripStarted).thenAnswer((_) => const Stream.empty());
  when(() => ws.onTripCompleted).thenAnswer((_) => const Stream.empty());
  when(() => ws.dispose()).thenReturn(null);
}

ProviderContainer _makeContainer(
  MockTripRepository mockRepo,
  MockTripWebSocketService mockWs,
) {
  return ProviderContainer(
    overrides: [
      tripRepositoryProvider.overrideWithValue(mockRepo),
      tripWebSocketProvider.overrideWithValue(mockWs),
    ],
  );
}

// ── Tests ─────────────────────────────────────────────────────────────────────

void main() {
  late MockTripRepository mockRepo;
  late MockTripWebSocketService mockWs;

  setUp(() {
    mockRepo = MockTripRepository();
    mockWs = MockTripWebSocketService();
    registerFallbackValue('trip-fallback');
  });

  // ── build ──────────────────────────────────────────────────────────────────

  group('build', () {
    test('sin viaje activo → estado idle', () async {
      when(() => mockRepo.getActiveTrip()).thenAnswer((_) async => null);

      final container = _makeContainer(mockRepo, mockWs);
      addTearDown(container.dispose);

      final state = await container.read(tripProvider.future);
      expect(state.flowStatus, equals(TripFlowStatus.idle));
      expect(state.currentTrip, isNull);
    });

    test('con viaje activo searching → estado searching', () async {
      final trip = _makeTrip(status: 'searching');
      when(() => mockRepo.getActiveTrip()).thenAnswer((_) async => trip);
      _stubIdleWs(mockWs);

      final container = _makeContainer(mockRepo, mockWs);
      addTearDown(container.dispose);

      final state = await container.read(tripProvider.future);
      expect(state.flowStatus, equals(TripFlowStatus.searching));
      expect(state.currentTrip?.id, equals('trip-1'));
    });

    test('con viaje activo in_progress → estado inProgress', () async {
      final trip = _makeTrip(status: 'in_progress');
      when(() => mockRepo.getActiveTrip()).thenAnswer((_) async => trip);
      _stubIdleWs(mockWs);

      final container = _makeContainer(mockRepo, mockWs);
      addTearDown(container.dispose);

      final state = await container.read(tripProvider.future);
      expect(state.flowStatus, equals(TripFlowStatus.inProgress));
    });

    test('error al consultar viaje activo → estado idle (no lanza)', () async {
      when(() => mockRepo.getActiveTrip()).thenThrow(Exception('Sin conexión'));

      final container = _makeContainer(mockRepo, mockWs);
      addTearDown(container.dispose);

      final state = await container.read(tripProvider.future);
      expect(state.flowStatus, equals(TripFlowStatus.idle));
    });
  });

  // ── createTrip ─────────────────────────────────────────────────────────────

  group('createTrip', () {
    test('éxito → estado searching con el viaje creado', () async {
      when(() => mockRepo.getActiveTrip()).thenAnswer((_) async => null);
      when(() => mockRepo.createTrip(
            originAddress: any(named: 'originAddress'),
            originLat: any(named: 'originLat'),
            originLng: any(named: 'originLng'),
            destAddress: any(named: 'destAddress'),
            destLat: any(named: 'destLat'),
            destLng: any(named: 'destLng'),
            proposedPrice: any(named: 'proposedPrice'),
            paymentMethod: any(named: 'paymentMethod'),
          )).thenAnswer((_) async => _makeTrip());
      _stubIdleWs(mockWs);

      final container = _makeContainer(mockRepo, mockWs);
      addTearDown(container.dispose);
      await container.read(tripProvider.future);

      final success = await container.read(tripProvider.notifier).createTrip(
            originAddress: 'Calle A',
            originLat: -14.79,
            originLng: -71.41,
            destAddress: 'Calle B',
            destLat: -14.80,
            destLng: -71.42,
            proposedPrice: '10.00',
          );

      expect(success, isTrue);
      final state = container.read(tripProvider).valueOrNull;
      expect(state?.flowStatus, equals(TripFlowStatus.searching));
      expect(state?.currentTrip?.id, equals('trip-1'));
      verify(() => mockWs.connect('trip-1')).called(1);
    });

    test('fallo → estado error', () async {
      when(() => mockRepo.getActiveTrip()).thenAnswer((_) async => null);
      when(() => mockRepo.createTrip(
            originAddress: any(named: 'originAddress'),
            originLat: any(named: 'originLat'),
            originLng: any(named: 'originLng'),
            destAddress: any(named: 'destAddress'),
            destLat: any(named: 'destLat'),
            destLng: any(named: 'destLng'),
            proposedPrice: any(named: 'proposedPrice'),
            paymentMethod: any(named: 'paymentMethod'),
          )).thenThrow(Exception('Sin conductores disponibles'));

      final container = _makeContainer(mockRepo, mockWs);
      addTearDown(container.dispose);
      await container.read(tripProvider.future);

      final success = await container.read(tripProvider.notifier).createTrip(
            originAddress: 'A',
            originLat: 0,
            originLng: 0,
            destAddress: 'B',
            destLat: 0,
            destLng: 0,
            proposedPrice: '5',
          );

      expect(success, isFalse);
      expect(container.read(tripProvider).hasError, isTrue);
    });
  });

  // ── acceptOffer ────────────────────────────────────────────────────────────

  group('acceptOffer', () {
    test('éxito → estado accepted con el viaje actualizado', () async {
      final trip = _makeTrip();
      final offer = _makeOffer();
      final acceptedTrip = _makeTrip(status: 'accepted');

      when(() => mockRepo.getActiveTrip()).thenAnswer((_) async => null);
      when(() => mockRepo.acceptOffer(
            tripId: any(named: 'tripId'),
            offerId: any(named: 'offerId'),
          )).thenAnswer((_) async => acceptedTrip);
      _stubIdleWs(mockWs);

      final container = _makeContainer(mockRepo, mockWs);
      addTearDown(container.dispose);
      await container.read(tripProvider.future);

      // Inyectar estado con viaje y ofertas
      container.read(tripProvider.notifier).state = AsyncValue.data(
        TripState.hasOffers(trip, [offer]),
      );

      final success =
          await container.read(tripProvider.notifier).acceptOffer(offer.id);

      expect(success, isTrue);
      final state = container.read(tripProvider).valueOrNull;
      expect(state?.flowStatus, equals(TripFlowStatus.accepted));
      expect(state?.selectedOffer?.id, equals(offer.id));
    });

    test('sin viaje activo → retorna false sin llamar al repo', () async {
      when(() => mockRepo.getActiveTrip()).thenAnswer((_) async => null);

      final container = _makeContainer(mockRepo, mockWs);
      addTearDown(container.dispose);
      await container.read(tripProvider.future);

      final success =
          await container.read(tripProvider.notifier).acceptOffer('offer-x');

      expect(success, isFalse);
      verifyNever(() => mockRepo.acceptOffer(
            tripId: any(named: 'tripId'),
            offerId: any(named: 'offerId'),
          ));
    });
  });

  // ── cancelTrip ─────────────────────────────────────────────────────────────

  group('cancelTrip', () {
    test('éxito → estado idle', () async {
      final trip = _makeTrip();
      when(() => mockRepo.getActiveTrip()).thenAnswer((_) async => null);
      when(() => mockRepo.cancelTrip(any()))
          .thenAnswer((_) async => _makeTrip(status: 'cancelled'));
      when(() => mockWs.dispose()).thenReturn(null);

      final container = _makeContainer(mockRepo, mockWs);
      addTearDown(container.dispose);
      await container.read(tripProvider.future);

      container.read(tripProvider.notifier).state =
          AsyncValue.data(TripState.searching(trip));

      final success = await container.read(tripProvider.notifier).cancelTrip();

      expect(success, isTrue);
      final state = container.read(tripProvider).valueOrNull;
      expect(state?.flowStatus, equals(TripFlowStatus.idle));
      expect(state?.currentTrip, isNull);
    });

    test('sin viaje activo → retorna false', () async {
      when(() => mockRepo.getActiveTrip()).thenAnswer((_) async => null);

      final container = _makeContainer(mockRepo, mockWs);
      addTearDown(container.dispose);
      await container.read(tripProvider.future);

      final success = await container.read(tripProvider.notifier).cancelTrip();

      expect(success, isFalse);
      verifyNever(() => mockRepo.cancelTrip(any()));
    });
  });

  // ── loadTripHistory ────────────────────────────────────────────────────────

  group('loadTripHistory', () {
    test('carga historial correctamente', () async {
      final trips = [_makeTrip(status: 'completed')];
      when(() => mockRepo.getActiveTrip()).thenAnswer((_) async => null);
      when(() => mockRepo.getTripHistory()).thenAnswer((_) async => trips);

      final container = _makeContainer(mockRepo, mockWs);
      addTearDown(container.dispose);
      await container.read(tripProvider.future);

      await container.read(tripProvider.notifier).loadTripHistory();

      final state = container.read(tripProvider).valueOrNull;
      expect(state?.tripHistory, hasLength(1));
      expect(state?.tripHistory.first.status, equals('completed'));
      expect(state?.isLoadingHistory, isFalse);
    });

    test('fallo al cargar historial → isLoadingHistory vuelve a false', () async {
      when(() => mockRepo.getActiveTrip()).thenAnswer((_) async => null);
      when(() => mockRepo.getTripHistory())
          .thenThrow(Exception('Sin conexión'));

      final container = _makeContainer(mockRepo, mockWs);
      addTearDown(container.dispose);
      await container.read(tripProvider.future);

      await container.read(tripProvider.notifier).loadTripHistory();

      final state = container.read(tripProvider).valueOrNull;
      expect(state?.isLoadingHistory, isFalse);
    });
  });

  // ── resetTrip ──────────────────────────────────────────────────────────────

  group('resetTrip', () {
    test('limpia viaje activo y vuelve al estado idle', () async {
      when(() => mockRepo.getActiveTrip()).thenAnswer((_) async => null);
      when(() => mockWs.dispose()).thenReturn(null);

      final container = _makeContainer(mockRepo, mockWs);
      addTearDown(container.dispose);
      await container.read(tripProvider.future);

      container.read(tripProvider.notifier).state =
          AsyncValue.data(TripState.searching(_makeTrip()));

      container.read(tripProvider.notifier).resetTrip();

      final state = container.read(tripProvider).valueOrNull;
      expect(state?.flowStatus, equals(TripFlowStatus.idle));
      expect(state?.currentTrip, isNull);
    });
  });
}
