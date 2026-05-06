import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:mocktail/mocktail.dart';

import 'package:espinargo_app/features/auth/data/models/user_model.dart';
import 'package:espinargo_app/features/auth/domain/providers/auth_provider.dart';
import 'package:espinargo_app/features/auth/data/repositories/auth_repository.dart';
import 'package:espinargo_app/features/profile/data/repositories/profile_repository.dart';
import 'package:espinargo_app/features/profile/domain/providers/profile_provider.dart';
import 'package:espinargo_app/features/profile/domain/providers/profile_state.dart';

// ── Mocks ─────────────────────────────────────────────────────────────────────

class MockProfileRepository extends Mock implements ProfileRepository {}
class MockAuthRepository extends Mock implements AuthRepository {}

// ── Fixtures ──────────────────────────────────────────────────────────────────

UserModel _makeUser({
  String fullName = 'Juan Quispe',
  String phoneNumber = '+51987654321',
}) =>
    UserModel(
      id: 'u-1',
      fullName: fullName,
      phoneNumber: phoneNumber,
      role: 'passenger',
      status: 'active',
      phoneVerified: true,
      preferredLang: 'es',
      createdAt: '2024-01-01T00:00:00Z',
    );

// ── Helper ────────────────────────────────────────────────────────────────────

ProviderContainer _makeContainer(
  MockProfileRepository mockProfileRepo,
  MockAuthRepository mockAuthRepo,
) {
  return ProviderContainer(
    overrides: [
      profileRepositoryProvider.overrideWithValue(mockProfileRepo),
      authRepositoryProvider.overrideWithValue(mockAuthRepo),
    ],
  );
}

// ── Tests ─────────────────────────────────────────────────────────────────────

void main() {
  late MockProfileRepository mockProfileRepo;
  late MockAuthRepository mockAuthRepo;

  setUp(() {
    mockProfileRepo = MockProfileRepository();
    mockAuthRepo = MockAuthRepository();
  });

  // ── build ──────────────────────────────────────────────────────────────────

  group('build', () {
    test('carga el perfil del usuario al inicializar', () async {
      final user = _makeUser();
      when(() => mockProfileRepo.getProfile()).thenAnswer((_) async => user);
      when(() => mockAuthRepo.getSavedTokens()).thenAnswer(
        (_) async => {'access_token': null, 'refresh_token': null},
      );

      final container = _makeContainer(mockProfileRepo, mockAuthRepo);
      addTearDown(container.dispose);

      final state = await container.read(profileProvider.future);
      expect(state.user.fullName, equals('Juan Quispe'));
      expect(state.isLoading, isFalse);
    });

    test('error al cargar perfil → profileProvider lanza', () async {
      when(() => mockProfileRepo.getProfile())
          .thenThrow(Exception('Sesión expirada'));
      when(() => mockAuthRepo.getSavedTokens()).thenAnswer(
        (_) async => {'access_token': null, 'refresh_token': null},
      );

      final container = _makeContainer(mockProfileRepo, mockAuthRepo);
      addTearDown(container.dispose);

      expect(
        () => container.read(profileProvider.future),
        throwsA(isA<Exception>()),
      );
    });
  });

  // ── updateProfile ──────────────────────────────────────────────────────────

  group('updateProfile', () {
    test('éxito → usuario actualizado en estado', () async {
      final original = _makeUser();
      final updated = _makeUser(fullName: 'Juan Actualizado');

      when(() => mockProfileRepo.getProfile()).thenAnswer((_) async => original);
      when(() => mockProfileRepo.updateProfile(
            fullName: any(named: 'fullName'),
            phoneNumber: any(named: 'phoneNumber'),
          )).thenAnswer((_) async => updated);
      when(() => mockAuthRepo.getSavedTokens()).thenAnswer(
        (_) async => {'access_token': null, 'refresh_token': null},
      );

      final container = _makeContainer(mockProfileRepo, mockAuthRepo);
      addTearDown(container.dispose);
      await container.read(profileProvider.future);

      final success = await container.read(profileProvider.notifier).updateProfile(
            fullName: 'Juan Actualizado',
            phone: '+51987654321',
          );

      expect(success, isTrue);
      final state = container.read(profileProvider).valueOrNull;
      expect(state?.user.fullName, equals('Juan Actualizado'));
      expect(state?.isLoading, isFalse);
    });

    test('fallo → errorMessage establecido, retorna false', () async {
      final user = _makeUser();
      when(() => mockProfileRepo.getProfile()).thenAnswer((_) async => user);
      when(() => mockProfileRepo.updateProfile(
            fullName: any(named: 'fullName'),
            phoneNumber: any(named: 'phoneNumber'),
          )).thenThrow(Exception('Datos inválidos'));
      when(() => mockAuthRepo.getSavedTokens()).thenAnswer(
        (_) async => {'access_token': null, 'refresh_token': null},
      );

      final container = _makeContainer(mockProfileRepo, mockAuthRepo);
      addTearDown(container.dispose);
      await container.read(profileProvider.future);

      final success = await container.read(profileProvider.notifier).updateProfile(
            fullName: '',
            phone: '',
          );

      expect(success, isFalse);
      final state = container.read(profileProvider).valueOrNull;
      expect(state?.errorMessage, isNotNull);
      expect(state?.isLoading, isFalse);
    });
  });
}
