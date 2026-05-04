import 'package:flutter_test/flutter_test.dart';
import 'package:espinargo_app/features/auth/data/models/user_model.dart';
import 'package:espinargo_app/features/auth/domain/providers/auth_state.dart';

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

void main() {
  group('AuthState factories', () {
    test('unauthenticated crea estado sin usuario y sin loading', () {
      final state = AuthState.unauthenticated();
      expect(state.status, equals(AuthStatus.unauthenticated));
      expect(state.user, isNull);
      expect(state.isLoading, isFalse);
      expect(state.errorMessage, isNull);
    });

    test('authenticated crea estado con usuario y sin loading', () {
      final user = _makeUser();
      final state = AuthState.authenticated(user);
      expect(state.status, equals(AuthStatus.authenticated));
      expect(state.user, equals(user));
      expect(state.isLoading, isFalse);
    });

    test('loading crea estado con isLoading true', () {
      final state = AuthState.loading();
      expect(state.status, equals(AuthStatus.loading));
      expect(state.isLoading, isTrue);
    });

    test('initial crea estado con isLoading true', () {
      final state = AuthState.initial();
      expect(state.status, equals(AuthStatus.initial));
      expect(state.isLoading, isTrue);
    });

    test('error crea estado con mensaje de error', () {
      final state = AuthState.error('Credenciales incorrectas');
      expect(state.status, equals(AuthStatus.error));
      expect(state.errorMessage, equals('Credenciales incorrectas'));
      expect(state.isLoading, isFalse);
    });
  });

  group('AuthState getters', () {
    test('isAuthenticated es true solo en estado authenticated', () {
      expect(AuthState.authenticated(_makeUser()).isAuthenticated, isTrue);
      expect(AuthState.unauthenticated().isAuthenticated, isFalse);
      expect(AuthState.loading().isAuthenticated, isFalse);
    });

    test('isPassenger es true cuando el rol es passenger', () {
      expect(
          AuthState.authenticated(_makeUser(role: 'passenger')).isPassenger,
          isTrue);
      expect(
          AuthState.authenticated(_makeUser(role: 'driver')).isPassenger,
          isFalse);
    });

    test('isDriver es true cuando el rol es driver', () {
      expect(
          AuthState.authenticated(_makeUser(role: 'driver')).isDriver, isTrue);
      expect(
          AuthState.authenticated(_makeUser(role: 'passenger')).isDriver,
          isFalse);
    });

    test('userRole retorna "passenger" cuando no hay usuario', () {
      expect(AuthState.unauthenticated().userRole, equals('passenger'));
    });

    test('userRole retorna el rol del usuario autenticado', () {
      expect(
          AuthState.authenticated(_makeUser(role: 'driver')).userRole,
          equals('driver'));
    });
  });

  group('AuthState.copyWith', () {
    test('actualiza solo el campo indicado', () {
      final state = AuthState.authenticated(_makeUser());
      final updated = state.copyWith(isLoading: true);
      expect(updated.isLoading, isTrue);
      expect(updated.user, equals(state.user));
      expect(updated.status, equals(state.status));
    });

    test('clearUser elimina el usuario del estado', () {
      final state = AuthState.authenticated(_makeUser());
      final updated = state.copyWith(clearUser: true);
      expect(updated.user, isNull);
    });

    test('actualiza selectedRole', () {
      final state = AuthState.unauthenticated();
      final updated = state.copyWith(selectedRole: 'driver');
      expect(updated.selectedRole, equals('driver'));
    });
  });
}
