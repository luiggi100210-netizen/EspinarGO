import '../../data/models/user_model.dart';

/// Estado de autenticación.
/// Representa todos los posibles estados del flujo de auth.
enum AuthStatus {
  /// App recién abierta, verificando sesión activa.
  initial,

  /// Procesando una operación (login, registro, etc.).
  loading,

  /// Usuario logueado y activo.
  authenticated,

  /// Sin sesión activa.
  unauthenticated,

  /// Ocurrió un error.
  error,
}

/// Estado inmutable de la autenticación con Riverpod.
/// El estado inmutable evita bugs difíciles de rastrear.
class AuthState {
  final AuthStatus status;
  final UserModel? user;
  final String? errorMessage;
  final bool isLoading;
  final String? selectedRole;

  const AuthState({
    this.status = AuthStatus.initial,
    this.user,
    this.errorMessage,
    this.isLoading = false,
    this.selectedRole,
  });

  /// Crea una copia del estado con campos actualizados.
  AuthState copyWith({
    AuthStatus? status,
    UserModel? user,
    bool clearUser = false,
    String? errorMessage,
    bool? isLoading,
    String? selectedRole,
  }) {
    return AuthState(
      status: status ?? this.status,
      user: clearUser ? null : (user ?? this.user),
      errorMessage: errorMessage,
      isLoading: isLoading ?? this.isLoading,
      selectedRole: selectedRole ?? this.selectedRole,
    );
  }

  /// True si el usuario está autenticado.
  bool get isAuthenticated => status == AuthStatus.authenticated;

  /// True si el usuario es pasajero.
  bool get isPassenger => user?.isPassenger ?? false;

  /// True si el usuario es conductor.
  bool get isDriver => user?.isDriver ?? false;

  /// Rol del usuario (default: passenger).
  String get userRole => user?.role ?? 'passenger';

  /// Estado inicial de carga (verificando sesión).
  factory AuthState.initial() => const AuthState(
        status: AuthStatus.initial,
        isLoading: true,
      );

  /// Estado de carga procesando una operación.
  factory AuthState.loading() => const AuthState(
        status: AuthStatus.loading,
        isLoading: true,
      );

  /// Estado autenticado con usuario.
  factory AuthState.authenticated(UserModel user) => AuthState(
        status: AuthStatus.authenticated,
        user: user,
        isLoading: false,
      );

  /// Estado sin sesión.
  factory AuthState.unauthenticated() => const AuthState(
        status: AuthStatus.unauthenticated,
        isLoading: false,
      );

  /// Estado con error.
  factory AuthState.error(String message) => AuthState(
        status: AuthStatus.error,
        errorMessage: message,
        isLoading: false,
      );

  @override
  String toString() {
    return 'AuthState(status: $status, user: ${user?.fullName}, isLoading: $isLoading, error: $errorMessage)';
  }
}