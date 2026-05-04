import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:mocktail/mocktail.dart';
import 'package:flutter_secure_storage/flutter_secure_storage.dart';

import 'package:espinargo_app/core/network/dio_client.dart';
import 'package:espinargo_app/features/auth/data/models/user_model.dart';
import 'package:espinargo_app/features/auth/data/models/auth_response_model.dart';
import 'package:espinargo_app/features/auth/data/repositories/auth_repository.dart';
import 'package:espinargo_app/features/auth/domain/providers/auth_provider.dart';
import 'package:espinargo_app/features/auth/domain/providers/auth_state.dart';

// ── Mocks ────────────────────────────────────────────────────────────────────

class MockAuthRepository extends Mock implements AuthRepository {}

// ── Fixtures ─────────────────────────────────────────────────────────────────

UserModel _makeUser({String role = 'passenger'}) => UserModel(
      id: 'u-1',
      fullName: 'Juan Quispe',
      phoneNumber: '+51987654321',
      role: role,
      status: 'active',
      phoneVerified: true,
      preferredLang: 'es',
      createdAt: '2024-01-01T00:00:00Z',
    );

TokenResponseModel _makeTokenResponse() => TokenResponseModel(
      accessToken: 'access_token',
      refreshToken: 'refresh_token',
      tokenType: 'Bearer',
      expiresIn: 1800,
      user: _makeUser(),
    );

// ── Helper ────────────────────────────────────────────────────────────────────

ProviderContainer _makeContainer(MockAuthRepository mockRepo) {
  return ProviderContainer(
    overrides: [
      authRepositoryProvider.overrideWithValue(mockRepo),
    ],
  );
}

void main() {
  late MockAuthRepository mockRepo;

  setUp(() {
    mockRepo = MockAuthRepository();
  });

  // Estado inicial: sin token → unauthenticated
  group('Estado inicial', () {
    test('sin token guardado → estado unauthenticated', () async {
      when(() => mockRepo.getSavedTokens()).thenAnswer(
        (_) async => {'access_token': null, 'refresh_token': null},
      );

      final container = _makeContainer(mockRepo);
      addTearDown(container.dispose);

      final state = await container.read(authProvider.future);
      expect(state.status, equals(AuthStatus.unauthenticated));
      expect(state.user, isNull);
    });

    test('con token válido → estado authenticated con usuario', () async {
      when(() => mockRepo.getSavedTokens()).thenAnswer(
        (_) async => {
          'access_token': 'valid_token',
          'refresh_token': 'refresh_token',
        },
      );
      when(() => mockRepo.getMyProfile()).thenAnswer(
        (_) async => _makeUser(),
      );

      final container = _makeContainer(mockRepo);
      addTearDown(container.dispose);

      final state = await container.read(authProvider.future);
      expect(state.status, equals(AuthStatus.authenticated));
      expect(state.user?.id, equals('u-1'));
    });

    test('con token expirado (getMyProfile lanza) → unauthenticated', () async {
      when(() => mockRepo.getSavedTokens()).thenAnswer(
        (_) async => {
          'access_token': 'expired_token',
          'refresh_token': 'refresh_token',
        },
      );
      when(() => mockRepo.getMyProfile())
          .thenThrow(Exception('Token expirado'));

      final container = _makeContainer(mockRepo);
      addTearDown(container.dispose);

      final state = await container.read(authProvider.future);
      expect(state.status, equals(AuthStatus.unauthenticated));
    });
  });

  // login
  group('login', () {
    test('éxito → estado authenticated con usuario', () async {
      when(() => mockRepo.getSavedTokens()).thenAnswer(
        (_) async => {'access_token': null, 'refresh_token': null},
      );
      when(() => mockRepo.login(
            phoneNumber: any(named: 'phoneNumber'),
            password: any(named: 'password'),
          )).thenAnswer((_) async => _makeTokenResponse());

      final container = _makeContainer(mockRepo);
      addTearDown(container.dispose);

      await container.read(authProvider.future);

      final success = await container
          .read(authProvider.notifier)
          .login('+51987654321', 'password123');

      expect(success, isTrue);
      final state = container.read(authProvider).valueOrNull;
      expect(state?.status, equals(AuthStatus.authenticated));
      expect(state?.user?.fullName, equals('Juan Quispe'));
    });

    test('fallo → estado error con mensaje limpio', () async {
      when(() => mockRepo.getSavedTokens()).thenAnswer(
        (_) async => {'access_token': null, 'refresh_token': null},
      );
      when(() => mockRepo.login(
            phoneNumber: any(named: 'phoneNumber'),
            password: any(named: 'password'),
          )).thenThrow(Exception('Credenciales incorrectas'));

      final container = _makeContainer(mockRepo);
      addTearDown(container.dispose);

      await container.read(authProvider.future);

      final success = await container
          .read(authProvider.notifier)
          .login('+51987654321', 'wrong');

      expect(success, isFalse);
      final asyncVal = container.read(authProvider);
      expect(asyncVal.hasError, isTrue);
      expect(asyncVal.error.toString(), equals('Credenciales incorrectas'));
    });
  });

  // register
  group('register', () {
    test('éxito → estado previo restaurado', () async {
      when(() => mockRepo.getSavedTokens()).thenAnswer(
        (_) async => {'access_token': null, 'refresh_token': null},
      );
      when(() => mockRepo.register(
            fullName: any(named: 'fullName'),
            phoneNumber: any(named: 'phoneNumber'),
            password: any(named: 'password'),
            role: any(named: 'role'),
          )).thenAnswer((_) async => RegisterResponseModel(
            message: 'ok',
            userId: 'u-1',
            phoneNumber: '+51987654321',
            nextStep: 'otp_verification',
          ));

      final container = _makeContainer(mockRepo);
      addTearDown(container.dispose);

      final stateBeforeRegister = await container.read(authProvider.future);

      final success = await container.read(authProvider.notifier).register(
            fullName: 'Juan Quispe',
            phoneNumber: '+51987654321',
            password: 'secret123',
            role: 'passenger',
          );

      expect(success, isTrue);
      final stateAfter = container.read(authProvider).valueOrNull;
      // Estado restaurado al previo (unauthenticated)
      expect(stateAfter?.status, equals(stateBeforeRegister.status));
    });

    test('fallo → mensaje sin prefijo Exception:', () async {
      when(() => mockRepo.getSavedTokens()).thenAnswer(
        (_) async => {'access_token': null, 'refresh_token': null},
      );
      when(() => mockRepo.register(
            fullName: any(named: 'fullName'),
            phoneNumber: any(named: 'phoneNumber'),
            password: any(named: 'password'),
            role: any(named: 'role'),
          )).thenThrow(Exception('El teléfono ya está registrado'));

      final container = _makeContainer(mockRepo);
      addTearDown(container.dispose);
      await container.read(authProvider.future);

      final success = await container.read(authProvider.notifier).register(
            fullName: 'Juan',
            phoneNumber: '+51987654321',
            password: 'secret',
            role: 'passenger',
          );

      expect(success, isFalse);
      final error = container.read(authProvider).error.toString();
      expect(error, equals('El teléfono ya está registrado'));
      expect(error, isNot(contains('Exception:')));
    });
  });

  // logout
  group('logout', () {
    test('cierra sesión y estado queda unauthenticated', () async {
      when(() => mockRepo.getSavedTokens()).thenAnswer(
        (_) async => {
          'access_token': 'tok',
          'refresh_token': 'ref',
        },
      );
      when(() => mockRepo.getMyProfile()).thenAnswer(
        (_) async => _makeUser(),
      );
      when(() => mockRepo.logout(any())).thenAnswer((_) async {});

      final container = _makeContainer(mockRepo);
      addTearDown(container.dispose);

      // Esperar a que build() complete (authenticated)
      final initialState = await container.read(authProvider.future);
      expect(initialState.status, equals(AuthStatus.authenticated));

      await container.read(authProvider.notifier).logout();

      final state = container.read(authProvider).valueOrNull;
      expect(state?.status, equals(AuthStatus.unauthenticated));
    });
  });

  // forgotPassword
  group('forgotPassword', () {
    test('éxito → retorna true y restaura estado previo', () async {
      when(() => mockRepo.getSavedTokens()).thenAnswer(
        (_) async => {'access_token': null, 'refresh_token': null},
      );
      when(() => mockRepo.forgotPassword(any())).thenAnswer(
        (_) async => MessageResponseModel(message: 'OTP enviado', success: true),
      );

      final container = _makeContainer(mockRepo);
      addTearDown(container.dispose);

      final prevState = await container.read(authProvider.future);
      final success = await container
          .read(authProvider.notifier)
          .forgotPassword('+51987654321');

      expect(success, isTrue);
      // Estado restaurado, no queda en loading
      expect(container.read(authProvider).isLoading, isFalse);
      expect(container.read(authProvider).valueOrNull?.status,
          equals(prevState.status));
    });

    test('fallo → retorna false y mensaje limpio', () async {
      when(() => mockRepo.getSavedTokens()).thenAnswer(
        (_) async => {'access_token': null, 'refresh_token': null},
      );
      when(() => mockRepo.forgotPassword(any()))
          .thenThrow(Exception('Número no encontrado'));

      final container = _makeContainer(mockRepo);
      addTearDown(container.dispose);
      await container.read(authProvider.future);

      final success = await container
          .read(authProvider.notifier)
          .forgotPassword('+51999999999');

      expect(success, isFalse);
      final error = container.read(authProvider).error.toString();
      expect(error, equals('Número no encontrado'));
      expect(error, isNot(contains('Exception:')));
    });
  });

  // verifyPhone
  group('verifyPhone', () {
    test('éxito → retorna true y restaura estado previo (no cambia a authenticated sin usuario)',
        () async {
      when(() => mockRepo.getSavedTokens()).thenAnswer(
        (_) async => {'access_token': null, 'refresh_token': null},
      );
      when(() => mockRepo.verifyPhone(
            phoneNumber: any(named: 'phoneNumber'),
            code: any(named: 'code'),
            purpose: any(named: 'purpose'),
          )).thenAnswer((_) async => true);

      final container = _makeContainer(mockRepo);
      addTearDown(container.dispose);

      final prevState = await container.read(authProvider.future);
      final success = await container
          .read(authProvider.notifier)
          .verifyPhone('+51987654321', '123456', 'phone_verify');

      expect(success, isTrue);
      // Estado restaurado: sigue siendo unauthenticated (no authenticated sin user)
      final state = container.read(authProvider).valueOrNull;
      expect(state?.status, equals(prevState.status));
      expect(state?.user, isNull);
    });
  });
}
