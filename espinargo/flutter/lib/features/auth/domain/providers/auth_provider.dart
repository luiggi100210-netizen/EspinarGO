import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:shared_preferences/shared_preferences.dart';

import '../../../../core/constants/storage_keys.dart';
import '../../../../core/providers.dart';
import '../../data/models/user_model.dart';
import '../../data/models/auth_response_model.dart';
import '../../data/repositories/auth_repository.dart';
import 'auth_state.dart';

/// Provider del repositorio de autenticación.
/// Inyecta las dependencias automáticamente con Riverpod.
final authRepositoryProvider = Provider<AuthRepository>((ref) {
  final dioClient = ref.watch(dioClientProvider);
  final secureStorage = ref.watch(secureStorageProvider);
  return AuthRepository(
    dioClient: dioClient,
    secureStorage: secureStorage,
  );
});

/// Provider principal de autenticación.
/// Usa AsyncNotifier para manejar el estado de forma reactiva.
final authProvider = AsyncNotifierProvider<AuthNotifier, AuthState>(() {
  return AuthNotifier();
});

/// Notificador de autenticación.
/// Maneja toda la lógica de auth y conecta UI con el repositorio.
class AuthNotifier extends AsyncNotifier<AuthState> {
  @override
  Future<AuthState> build() async {
    // Cuando el interceptor detecta sesión expirada, forzar logout en la UI.
    ref.listen(sessionExpiredProvider, (_, __) {
      state = AsyncValue.data(AuthState.unauthenticated());
    });
    return await _checkExistingSession();
  }

  /// Verifica si hay una sesión activa al abrir la app.
  Future<AuthState> _checkExistingSession() async {
    final repository = ref.read(authRepositoryProvider);

    try {
      final tokens = await repository.getSavedTokens();
      final accessToken = tokens['access_token'];

      // No hay sesión activa
      if (accessToken == null) {
        return AuthState.unauthenticated();
      }

      // Verificar que el token sigue siendo válido
      try {
        final user = await repository.getMyProfile();
        return AuthState.authenticated(user);
      } catch (_) {
        // El token ya no es válido
        return AuthState.unauthenticated();
      }
    } catch (e) {
      return AuthState.unauthenticated();
    }
  }

  /// Registra un nuevo usuario.
  /// Retorna true si el registro fue exitoso (para navegar al OTP).
  Future<bool> register({
    required String fullName,
    required String phoneNumber,
    required String password,
    required String role,
    String? email,
  }) async {
    final previousState = state;
    state = const AsyncValue.loading();

    try {
      final repository = ref.read(authRepositoryProvider);
      await repository.register(
        fullName: fullName,
        phoneNumber: phoneNumber,
        password: password,
        role: role,
        email: email,
      );

      state = previousState;
      return true;
    } catch (e) {
      state = AsyncValue.error(
        e.toString().replaceFirst('Exception: ', ''),
        StackTrace.current,
      );
      return false;
    }
  }

  /// Envía un código OTP al teléfono.
  Future<OTPResponseModel?> sendOTP(String phone, String purpose) async {
    final previousState = state;
    state = const AsyncValue.loading();

    try {
      final repository = ref.read(authRepositoryProvider);
      final response = await repository.sendOTP(
        phoneNumber: phone,
        purpose: purpose,
      );
      state = previousState;
      return response;
    } catch (e) {
      state = AsyncValue.error(
        e.toString().replaceFirst('Exception: ', ''),
        StackTrace.current,
      );
      return null;
    }
  }

  /// Verifica el código OTP.
  Future<bool> verifyPhone(String phone, String code, String purpose) async {
    final previousState = state;
    state = const AsyncValue.loading();

    try {
      final repository = ref.read(authRepositoryProvider);
      final result = await repository.verifyPhone(
        phoneNumber: phone,
        code: code,
        purpose: purpose,
      );

      // La verificación solo confirma el teléfono; la navegación maneja el siguiente paso.
      state = previousState;
      return result;
    } catch (e) {
      state = AsyncValue.error(
        e.toString().replaceFirst('Exception: ', ''),
        StackTrace.current,
      );
      return false;
    }
  }

  /// Inicia sesión del usuario.
  Future<bool> login(String phone, String password) async {
    state = const AsyncValue.loading();

    try {
      final repository = ref.read(authRepositoryProvider);
      final tokenResponse = await repository.login(
        phoneNumber: phone,
        password: password,
      );

      state = AsyncValue.data(AuthState.authenticated(tokenResponse.user));
      return true;
    } catch (e) {
      state = AsyncValue.error(
        e.toString().replaceFirst('Exception: ', ''),
        StackTrace.current,
      );
      return false;
    }
  }

  /// Cierra la sesión del usuario.
  Future<void> logout() async {
    final repository = ref.read(authRepositoryProvider);

    try {
      final tokens = await repository.getSavedTokens();
      final refreshToken = tokens['refresh_token'];

      if (refreshToken != null) {
        await repository.logout(refreshToken);
      }
    } catch (_) {
      // Continuar con la limpieza aunque falle el server
    } finally {
      state = AsyncValue.data(AuthState.unauthenticated());
    }
  }

  /// Solicita recuperación de contraseña.
  Future<bool> forgotPassword(String phone) async {
    final previousState = state;
    state = const AsyncValue.loading();

    try {
      final repository = ref.read(authRepositoryProvider);
      await repository.forgotPassword(phone);
      state = previousState;
      return true;
    } catch (e) {
      state = AsyncValue.error(
        e.toString().replaceFirst('Exception: ', ''),
        StackTrace.current,
      );
      return false;
    }
  }

  /// Restablece la contraseña.
  Future<bool> resetPassword(String phone, String otp, String newPass) async {
    final previousState = state;
    state = const AsyncValue.loading();

    try {
      final repository = ref.read(authRepositoryProvider);
      await repository.resetPassword(
        phoneNumber: phone,
        otpCode: otp,
        newPassword: newPass,
      );
      state = previousState;
      return true;
    } catch (e) {
      state = AsyncValue.error(
        e.toString().replaceFirst('Exception: ', ''),
        StackTrace.current,
      );
      return false;
    }
  }

  /// Limpia el error del estado.
  void clearError() {
    final currentState = state.valueOrNull;
    if (currentState != null) {
      state = AsyncValue.data(currentState.copyWith(errorMessage: null));
    }
  }

  /// Guarda el rol seleccionado en RoleSelectionScreen.
  void setSelectedRole(String role) {
    final currentState = state.valueOrNull;
    if (currentState != null) {
      state = AsyncValue.data(currentState.copyWith(selectedRole: role));
    }
  }

  /// Actualiza el estado del usuario (para después de OTP verificado).
  void updateUser(UserModel user) {
    state = AsyncValue.data(AuthState.authenticated(user));
  }
}

/// Provider para verificar si es el primer lanzamiento de la app.
final isFirstLaunchProvider = FutureProvider<bool>((ref) async {
  final prefs = await SharedPreferences.getInstance();
  final isFirst = prefs.getBool(StorageKeys.IS_FIRST_LAUNCH) ?? true;
  if (isFirst) {
    await prefs.setBool(StorageKeys.IS_FIRST_LAUNCH, false);
  }
  return isFirst;
});