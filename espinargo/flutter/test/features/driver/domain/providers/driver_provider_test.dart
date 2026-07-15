import 'dart:async';

import 'package:flutter/services.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:mocktail/mocktail.dart';

import 'package:espinargo_app/features/auth/data/models/user_model.dart';
import 'package:espinargo_app/features/driver/data/models/driver_profile_model.dart';
import 'package:espinargo_app/features/driver/data/repositories/driver_repository.dart';
import 'package:espinargo_app/features/driver/data/services/driver_websocket_service.dart';
import 'package:espinargo_app/features/driver/domain/providers/driver_provider.dart';
import 'package:espinargo_app/features/driver/domain/providers/driver_state.dart';
import 'package:espinargo_app/features/trips/data/models/trip_model.dart';
import 'package:espinargo_app/features/trips/data/models/trip_offer_model.dart';

// ── Mocks ─────────────────────────────────────────────────────────────────────

class MockDriverRepository extends Mock implements DriverRepository {}
class MockDriverWebSocketService extends Mock implements DriverWebSocketService {}

// ── Fixtures ──────────────────────────────────────────────────────────────────

DriverProfileModel _makeProfile({bool isOnline = false, String status = 'approved'}) =>
    DriverProfileModel(
      id: 'dp-1',
      userId: 'u-1',
      driverStatus: status,
      isOnline: isOnline,
      totalTrips: 5,
      rating: 45,
      ratingCount: 10,
    );

TripModel _makeTrip({String id = 'trip-1', String status = 'accepted'}) => TripModel(
      id: id,
      originAddress: 'Calle A',
      originLat: '-14.79',
      originLng: '-71.41',
      destAddress: 'Calle B',
      destLat: '-14.80',
      destLng: '-71.42',
      proposedPrice: '8.00',
      status: status,
      paymentMethod: 'cash',
      createdAt: '2024-01-01T00:00:00Z',
    );

TripOfferModel _makeOffer() => TripOfferModel(
      id: 'offer-1',
      tripId: 'trip-1',
      driver: const UserModel(
        id: 'u-1',
        fullName: 'Carlos',
        phoneNumber: '+51976543210',
        role: 'driver',
        status: 'active',
        phoneVerified: true,
        preferredLang: 'es',
        createdAt: '2024-01-01T00:00:00Z',
      ),
      offeredPrice: '7.50',
      expiresAt: DateTime.now().add(const Duration(minutes: 5)).toIso8601String(),
      createdAt: '2024-01-01T00:00:00Z',
    );

// ── Helper ────────────────────────────────────────────────────────────────────

void _stubIdleWs(MockDriverWebSocketService ws) {
  when(() => ws.connect()).thenAnswer((_) async {});
  when(() => ws.onNewTripRequest).thenAnswer((_) => const Stream.empty());
  when(() => ws.onTripCancelled).thenAnswer((_) => const Stream.empty());
  when(() => ws.onOfferAccepted).thenAnswer((_) => const Stream.empty());
  when(() => ws.disconnect()).thenReturn(null);
  when(() => ws.dispose()).thenReturn(null);
}

ProviderContainer _makeContainer(
  MockDriverRepository mockRepo,
  MockDriverWebSocketService mockWs,
) {
  return ProviderContainer(
    overrides: [
      driverRepositoryProvider.overrideWithValue(mockRepo),
      driverWebSocketProvider.overrideWithValue(mockWs),
    ],
  );
}

// ── Tests ─────────────────────────────────────────────────────────────────────

void main() {
  late MockDriverRepository mockRepo;
  late MockDriverWebSocketService mockWs;

  setUpAll(() {
    TestWidgetsFlutterBinding.ensureInitialized();
    // Silence MissingPluginException from geolocator in unit tests
    TestDefaultBinaryMessengerBinding.instance.defaultBinaryMessenger
        .setMockMethodCallHandler(
      const MethodChannel('flutter.baseflow.com/geolocator'),
      (call) async => null,
    );
  });

  setUp(() {
    mockRepo = MockDriverRepository();
    mockWs = MockDriverWebSocketService();
  });

  // ── build ──────────────────────────────────────────────────────────────────

  group('build', () {
    test('conductor offline → estado offline', () async {
      when(() => mockRepo.getMyDriverProfile())
          .thenAnswer((_) async => _makeProfile(isOnline: false));

      final container = _makeContainer(mockRepo, mockWs);
      addTearDown(container.dispose);

      final state = await container.read(driverProvider.future);
      expect(state.flowStatus, equals(DriverFlowStatus.offline));
      expect(state.driverProfile?.id, equals('dp-1'));
    });

    test('conductor online → estado online y WS conectado', () async {
      when(() => mockRepo.getMyDriverProfile())
          .thenAnswer((_) async => _makeProfile(isOnline: true));
      _stubIdleWs(mockWs);

      final container = _makeContainer(mockRepo, mockWs);
      addTearDown(container.dispose);

      final state = await container.read(driverProvider.future);
      expect(state.flowStatus, equals(DriverFlowStatus.online));
      verify(() => mockWs.connect()).called(1);
    });

    test('error al cargar perfil → estado offline sin lanzar', () async {
      when(() => mockRepo.getMyDriverProfile())
          .thenThrow(Exception('Sin conexión'));

      final container = _makeContainer(mockRepo, mockWs);
      addTearDown(container.dispose);

      final state = await container.read(driverProvider.future);
      expect(state.flowStatus, equals(DriverFlowStatus.offline));
    });
  });

  // ── toggleOnline ───────────────────────────────────────────────────────────

  group('toggleOnline', () {
    test('offline → online: llama setOnlineStatus(true) y conecta WS', () async {
      final profile = _makeProfile(isOnline: false);
      final onlineProfile = _makeProfile(isOnline: true);

      when(() => mockRepo.getMyDriverProfile()).thenAnswer((_) async => profile);
      when(() => mockRepo.setOnlineStatus(true)).thenAnswer((_) async => onlineProfile);
      _stubIdleWs(mockWs);

      final container = _makeContainer(mockRepo, mockWs);
      addTearDown(container.dispose);
      await container.read(driverProvider.future);

      await container.read(driverProvider.notifier).toggleOnline();

      final state = container.read(driverProvider).valueOrNull;
      expect(state?.flowStatus, equals(DriverFlowStatus.online));
      verify(() => mockRepo.setOnlineStatus(true)).called(1);
      verify(() => mockWs.connect()).called(1);
    });

    test('online → offline: llama setOnlineStatus(false) y desconecta WS', () async {
      final profile = _makeProfile(isOnline: true);
      final offlineProfile = _makeProfile(isOnline: false);

      when(() => mockRepo.getMyDriverProfile()).thenAnswer((_) async => profile);
      when(() => mockRepo.setOnlineStatus(false)).thenAnswer((_) async => offlineProfile);
      _stubIdleWs(mockWs);

      final container = _makeContainer(mockRepo, mockWs);
      addTearDown(container.dispose);
      await container.read(driverProvider.future);

      await container.read(driverProvider.notifier).toggleOnline();

      final state = container.read(driverProvider).valueOrNull;
      expect(state?.flowStatus, equals(DriverFlowStatus.offline));
      verify(() => mockRepo.setOnlineStatus(false)).called(1);
      verify(() => mockWs.disconnect()).called(1);
    });
  });

  // ── makeOffer ──────────────────────────────────────────────────────────────

  group('makeOffer', () {
    test('éxito → estado negotiating con oferta', () async {
      when(() => mockRepo.getMyDriverProfile())
          .thenAnswer((_) async => _makeProfile(isOnline: false));
      when(() => mockRepo.makeOffer(
            tripId: any(named: 'tripId'),
            offeredPrice: any(named: 'offeredPrice'),
            message: any(named: 'message'),
          )).thenAnswer((_) async => _makeOffer());

      final container = _makeContainer(mockRepo, mockWs);
      addTearDown(container.dispose);
      await container.read(driverProvider.future);

      final success = await container.read(driverProvider.notifier).makeOffer(
            tripId: 'trip-1',
            price: '7.50',
          );

      expect(success, isTrue);
      final state = container.read(driverProvider).valueOrNull;
      expect(state?.flowStatus, equals(DriverFlowStatus.negotiating));
      expect(state?.myOffer?.id, equals('offer-1'));
    });

    test('fallo → retorna false, estado no cambia', () async {
      when(() => mockRepo.getMyDriverProfile())
          .thenAnswer((_) async => _makeProfile(isOnline: false));
      when(() => mockRepo.makeOffer(
            tripId: any(named: 'tripId'),
            offeredPrice: any(named: 'offeredPrice'),
            message: any(named: 'message'),
          )).thenThrow(Exception('Viaje ya no disponible'));

      final container = _makeContainer(mockRepo, mockWs);
      addTearDown(container.dispose);
      await container.read(driverProvider.future);

      final success = await container.read(driverProvider.notifier).makeOffer(
            tripId: 'trip-1',
            price: '7.50',
          );

      expect(success, isFalse);
      final state = container.read(driverProvider).valueOrNull;
      expect(state?.flowStatus, equals(DriverFlowStatus.offline));
    });
  });

  // ── rejectRequest ──────────────────────────────────────────────────────────

  group('rejectRequest', () {
    test('elimina la solicitud de la lista', () async {
      when(() => mockRepo.getMyDriverProfile())
          .thenAnswer((_) async => _makeProfile(isOnline: false));

      final container = _makeContainer(mockRepo, mockWs);
      addTearDown(container.dispose);
      await container.read(driverProvider.future);

      // Inyectar estado con solicitudes pendientes
      container.read(driverProvider.notifier).state = AsyncValue.data(
        DriverState(
          flowStatus: DriverFlowStatus.receivedRequest,
          pendingRequests: [
            {'trip_id': 'trip-1', 'origin': 'A'},
            {'trip_id': 'trip-2', 'origin': 'B'},
          ],
        ),
      );

      container.read(driverProvider.notifier).rejectRequest('trip-1');

      final state = container.read(driverProvider).valueOrNull;
      expect(state?.pendingRequests, hasLength(1));
      expect(state?.pendingRequests.first['trip_id'], equals('trip-2'));
    });

    test('última solicitud rechazada → estado vuelve a online', () async {
      when(() => mockRepo.getMyDriverProfile())
          .thenAnswer((_) async => _makeProfile(isOnline: false));

      final container = _makeContainer(mockRepo, mockWs);
      addTearDown(container.dispose);
      await container.read(driverProvider.future);

      container.read(driverProvider.notifier).state = AsyncValue.data(
        const DriverState(
          flowStatus: DriverFlowStatus.receivedRequest,
          pendingRequests: [
            {'trip_id': 'trip-1'},
          ],
        ),
      );

      container.read(driverProvider.notifier).rejectRequest('trip-1');

      final state = container.read(driverProvider).valueOrNull;
      expect(state?.pendingRequests, isEmpty);
      expect(state?.flowStatus, equals(DriverFlowStatus.online));
    });
  });

  // ── startTrip ─────────────────────────────────────────────────────────────

  group('startTrip', () {
    test('éxito → estado passengerOnboard', () async {
      final trip = _makeTrip(status: 'in_progress');
      when(() => mockRepo.getMyDriverProfile())
          .thenAnswer((_) async => _makeProfile(isOnline: false));
      when(() => mockRepo.startTrip(any())).thenAnswer((_) async => trip);

      final container = _makeContainer(mockRepo, mockWs);
      addTearDown(container.dispose);
      await container.read(driverProvider.future);

      final success =
          await container.read(driverProvider.notifier).startTrip('trip-1');

      expect(success, isTrue);
      final state = container.read(driverProvider).valueOrNull;
      expect(state?.flowStatus, equals(DriverFlowStatus.passengerOnboard));
      expect(state?.currentTrip?.id, equals('trip-1'));
    });
  });

  // ── completeTrip ───────────────────────────────────────────────────────────

  group('completeTrip', () {
    test('éxito → estado completed y ganancias actualizadas', () async {
      final completedTrip = _makeTrip(status: 'completed').copyWith(finalPrice: '8.00');
      when(() => mockRepo.getMyDriverProfile())
          .thenAnswer((_) async => _makeProfile(isOnline: false));
      when(() => mockRepo.completeTrip(any())).thenAnswer((_) async => completedTrip);

      final container = _makeContainer(mockRepo, mockWs);
      addTearDown(container.dispose);
      await container.read(driverProvider.future);

      final success =
          await container.read(driverProvider.notifier).completeTrip('trip-1');

      expect(success, isTrue);
      final state = container.read(driverProvider).valueOrNull;
      expect(state?.flowStatus, equals(DriverFlowStatus.completed));
      expect(state?.todayTrips, equals(1));
      expect(state?.todayEarnings, equals(8.0));
    });
  });

  // ── cancelTrip ────────────────────────────────────────────────────────────

  group('cancelTrip', () {
    test('éxito → limpia viaje y vuelve a online', () async {
      when(() => mockRepo.getMyDriverProfile())
          .thenAnswer((_) async => _makeProfile(isOnline: false));
      when(() => mockRepo.cancelTrip(any()))
          .thenAnswer((_) async => _makeTrip(status: 'cancelled'));

      final container = _makeContainer(mockRepo, mockWs);
      addTearDown(container.dispose);
      await container.read(driverProvider.future);

      container.read(driverProvider.notifier).state = AsyncValue.data(
        DriverState(
          flowStatus: DriverFlowStatus.offerAccepted,
          currentTrip: _makeTrip(),
        ),
      );

      final success =
          await container.read(driverProvider.notifier).cancelTrip('trip-1');

      expect(success, isTrue);
      final state = container.read(driverProvider).valueOrNull;
      expect(state?.flowStatus, equals(DriverFlowStatus.online));
      expect(state?.currentTrip, isNull);
      expect(state?.myOffer, isNull);
    });
  });

  // ── loadEarnings ───────────────────────────────────────────────────────────

  group('loadEarnings', () {
    test('carga ganancias del día correctamente', () async {
      when(() => mockRepo.getMyDriverProfile())
          .thenAnswer((_) async => _makeProfile(isOnline: false));
      // Contrato real del backend: DriverEarningsResponse (schemas/trip.py)
      when(() => mockRepo.getDriverEarnings()).thenAnswer((_) async => {
            'total_earnings': '120.00',
            'total_trips': 3,
            'this_week_earnings': '42.50',
            'this_month_earnings': '80.00',
          });

      final container = _makeContainer(mockRepo, mockWs);
      addTearDown(container.dispose);
      await container.read(driverProvider.future);

      await container.read(driverProvider.notifier).loadEarnings();

      final state = container.read(driverProvider).valueOrNull;
      expect(state?.todayEarnings, equals(42.5));
      expect(state?.todayTrips, equals(3));
    });

    test('error al cargar ganancias → estado no cambia', () async {
      when(() => mockRepo.getMyDriverProfile())
          .thenAnswer((_) async => _makeProfile(isOnline: false));
      when(() => mockRepo.getDriverEarnings())
          .thenThrow(Exception('Sin conexión'));

      final container = _makeContainer(mockRepo, mockWs);
      addTearDown(container.dispose);
      await container.read(driverProvider.future);

      await container.read(driverProvider.notifier).loadEarnings();

      final state = container.read(driverProvider).valueOrNull;
      expect(state?.todayEarnings, equals(0.0));
    });
  });
}
