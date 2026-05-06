import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:mocktail/mocktail.dart';

import 'package:espinargo_app/features/packages/data/models/package_model.dart';
import 'package:espinargo_app/features/packages/data/models/tracking_event_model.dart';
import 'package:espinargo_app/features/packages/data/repositories/package_repository.dart';
import 'package:espinargo_app/features/packages/domain/providers/package_provider.dart';
import 'package:espinargo_app/features/packages/domain/providers/package_state.dart';

// ── Mocks ─────────────────────────────────────────────────────────────────────

class MockPackageRepository extends Mock implements PackageRepository {}

// ── Fixtures ──────────────────────────────────────────────────────────────────

PackageModel _makePackage({
  String id = 'pkg-1',
  String trackingCode = 'TRK001',
  String status = 'pending',
}) =>
    PackageModel(
      id: id,
      trackingCode: trackingCode,
      recipientName: 'Ana García',
      recipientPhone: '+51987654321',
      deliveryAddress: 'Av. Principal 123',
      size: 'medium',
      description: 'Ropa',
      status: status,
      paymentMethod: 'cash',
      createdAt: '2024-01-01T00:00:00Z',
    );

TrackingEventModel _makeEvent() => const TrackingEventModel(
      id: 'evt-1',
      status: 'pending',
      description: 'Paquete registrado',
      createdAt: '2024-01-01T00:00:00Z',
    );

// ── Helper ────────────────────────────────────────────────────────────────────

ProviderContainer _makeContainer(MockPackageRepository mockRepo) {
  return ProviderContainer(
    overrides: [
      packageRepositoryProvider.overrideWithValue(mockRepo),
    ],
  );
}

// ── Tests ─────────────────────────────────────────────────────────────────────

void main() {
  late MockPackageRepository mockRepo;

  setUp(() => mockRepo = MockPackageRepository());

  // ── build ──────────────────────────────────────────────────────────────────

  group('build', () {
    test('carga encomiendas del usuario al inicializar', () async {
      final packages = [_makePackage(), _makePackage(id: 'pkg-2', trackingCode: 'TRK002')];
      when(() => mockRepo.getMyPackages()).thenAnswer((_) async => packages);

      final container = _makeContainer(mockRepo);
      addTearDown(container.dispose);

      final state = await container.read(packageProvider.future);
      expect(state.myPackages, hasLength(2));
      expect(state.myPackages.first.id, equals('pkg-1'));
    });

    test('error al cargar → estado vacío, sin lanzar', () async {
      when(() => mockRepo.getMyPackages()).thenThrow(Exception('Sin conexión'));

      final container = _makeContainer(mockRepo);
      addTearDown(container.dispose);

      final state = await container.read(packageProvider.future);
      expect(state.myPackages, isEmpty);
      expect(state.flowStatus, equals(PackageFlowStatus.idle));
    });
  });

  // ── createPackage ──────────────────────────────────────────────────────────

  group('createPackage', () {
    test('éxito → paquete agregado al inicio de la lista', () async {
      final existing = _makePackage(id: 'pkg-0', trackingCode: 'TRK000');
      final newPkg = _makePackage();

      when(() => mockRepo.getMyPackages()).thenAnswer((_) async => [existing]);
      when(() => mockRepo.createPackage(
            recipientName: any(named: 'recipientName'),
            recipientPhone: any(named: 'recipientPhone'),
            deliveryAddress: any(named: 'deliveryAddress'),
            size: any(named: 'size'),
            description: any(named: 'description'),
            isFragile: any(named: 'isFragile'),
            paymentMethod: any(named: 'paymentMethod'),
          )).thenAnswer((_) async => newPkg);

      final container = _makeContainer(mockRepo);
      addTearDown(container.dispose);
      await container.read(packageProvider.future);

      final success = await container.read(packageProvider.notifier).createPackage(
            recipientName: 'Ana',
            recipientPhone: '+51987654321',
            deliveryAddress: 'Av. Principal 123',
            size: 'medium',
            description: 'Ropa',
          );

      expect(success, isTrue);
      final state = container.read(packageProvider).valueOrNull;
      expect(state?.flowStatus, equals(PackageFlowStatus.created));
      expect(state?.lastCreatedPackage?.id, equals('pkg-1'));
      expect(state?.myPackages.first.id, equals('pkg-1'));
      expect(state?.myPackages, hasLength(2));
    });

    test('fallo → errorMessage establecido, retorna false', () async {
      when(() => mockRepo.getMyPackages()).thenAnswer((_) async => []);
      when(() => mockRepo.createPackage(
            recipientName: any(named: 'recipientName'),
            recipientPhone: any(named: 'recipientPhone'),
            deliveryAddress: any(named: 'deliveryAddress'),
            size: any(named: 'size'),
            description: any(named: 'description'),
            isFragile: any(named: 'isFragile'),
            paymentMethod: any(named: 'paymentMethod'),
          )).thenThrow(Exception('Datos inválidos'));

      final container = _makeContainer(mockRepo);
      addTearDown(container.dispose);
      await container.read(packageProvider.future);

      final success = await container.read(packageProvider.notifier).createPackage(
            recipientName: 'Ana',
            recipientPhone: '+51987654321',
            deliveryAddress: 'Av.',
            size: 'small',
            description: 'Test',
          );

      expect(success, isFalse);
      final state = container.read(packageProvider).valueOrNull;
      expect(state?.errorMessage, isNotNull);
      expect(state?.isCreating, isFalse);
    });
  });

  // ── trackPackage ───────────────────────────────────────────────────────────

  group('trackPackage', () {
    test('éxito → estado tracked con paquete e historial', () async {
      final pkg = _makePackage(status: 'in_transit');
      final events = [_makeEvent()];

      when(() => mockRepo.getMyPackages()).thenAnswer((_) async => []);
      when(() => mockRepo.trackPackage(any())).thenAnswer((_) async => {
            'package': pkg,
            'tracking_history': events,
          });

      final container = _makeContainer(mockRepo);
      addTearDown(container.dispose);
      await container.read(packageProvider.future);

      await container.read(packageProvider.notifier).trackPackage('TRK001');

      final state = container.read(packageProvider).valueOrNull;
      expect(state?.flowStatus, equals(PackageFlowStatus.tracked));
      expect(state?.trackedPackage?.trackingCode, equals('TRK001'));
      expect(state?.trackingHistory, hasLength(1));
    });

    test('código inválido → errorMessage establecido', () async {
      when(() => mockRepo.getMyPackages()).thenAnswer((_) async => []);
      when(() => mockRepo.trackPackage(any()))
          .thenThrow(Exception('Código de seguimiento inválido'));

      final container = _makeContainer(mockRepo);
      addTearDown(container.dispose);
      await container.read(packageProvider.future);

      await container.read(packageProvider.notifier).trackPackage('INVALID');

      final state = container.read(packageProvider).valueOrNull;
      expect(state?.errorMessage, contains('inválido'));
      expect(state?.isTracking, isFalse);
    });
  });

  // ── clearError ─────────────────────────────────────────────────────────────

  group('clearError', () {
    test('limpia errorMessage del estado', () async {
      when(() => mockRepo.getMyPackages()).thenAnswer((_) async => []);

      final container = _makeContainer(mockRepo);
      addTearDown(container.dispose);
      await container.read(packageProvider.future);

      container.read(packageProvider.notifier).state = AsyncValue.data(
        const PackageState(errorMessage: 'Error previo'),
      );

      container.read(packageProvider.notifier).clearError();

      final state = container.read(packageProvider).valueOrNull;
      expect(state?.errorMessage, isNull);
    });
  });
}
