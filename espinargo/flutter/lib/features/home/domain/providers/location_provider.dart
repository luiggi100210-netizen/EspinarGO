import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:geolocator/geolocator.dart';
import 'package:google_maps_flutter/google_maps_flutter.dart';

import '../../data/services/location_service.dart';

/// Estado de la ubicación del usuario.
class LocationState {
  final Position? currentPosition;
  final LatLng? currentLatLng;
  final bool isLoading;
  final bool hasPermission;
  final bool isGpsEnabled;
  final String? errorMessage;

  const LocationState({
    this.currentPosition,
    this.currentLatLng,
    this.isLoading = false,
    this.hasPermission = false,
    this.isGpsEnabled = false,
    this.errorMessage,
  });

  LocationState copyWith({
    Position? currentPosition,
    LatLng? currentLatLng,
    bool? isLoading,
    bool? hasPermission,
    bool? isGpsEnabled,
    String? errorMessage,
  }) {
    return LocationState(
      currentPosition: currentPosition ?? this.currentPosition,
      currentLatLng: currentLatLng ?? this.currentLatLng,
      isLoading: isLoading ?? this.isLoading,
      hasPermission: hasPermission ?? this.hasPermission,
      isGpsEnabled: isGpsEnabled ?? this.isGpsEnabled,
      errorMessage: errorMessage,
    );
  }
}

/// Provider de ubicación del usuario.
final locationProvider = AsyncNotifierProvider<LocationNotifier, LocationState>(() {
  return LocationNotifier();
});

/// Notificador de ubicación.
/// Maneja el estado de la ubicación y la escucha en tiempo real.
class LocationNotifier extends AsyncNotifier<LocationState> {
  @override
  Future<LocationState> build() async {
    return _initialize();
  }

  /// Inicializa la ubicación al abrir la app.
  Future<LocationState> _initialize() async {
    state = const AsyncValue.loading();

    // Verificar si el GPS está habilitado
    final isGpsEnabled = await LocationService.isLocationEnabled();

    if (!isGpsEnabled) {
      return LocationState(
        isLoading: false,
        isGpsEnabled: false,
        hasPermission: false,
        currentLatLng: LocationService.espinarCenter(),
        errorMessage: 'Activa el GPS para usar la app',
      );
    }

    // Solicitar permisos
    final hasPermission = await LocationService.requestPermission();

    if (!hasPermission) {
      return LocationState(
        isLoading: false,
        isGpsEnabled: true,
        hasPermission: false,
        currentLatLng: LocationService.espinarCenter(),
        errorMessage: 'Se necesita permiso de ubicación',
      );
    }

    // Obtener posición actual
    final position = await LocationService.getCurrentPosition();

    if (position != null) {
      return LocationState(
        isLoading: false,
        isGpsEnabled: true,
        hasPermission: true,
        currentPosition: position,
        currentLatLng: LatLng(position.latitude, position.longitude),
      );
    }

    return LocationState(
      isLoading: false,
      isGpsEnabled: true,
      hasPermission: true,
      currentLatLng: LocationService.espinarCenter(),
      errorMessage: 'No se pudo obtener tu ubicación',
    );
  }

  /// Solicita permiso y obtiene la ubicación actual.
  Future<void> requestPermissionAndGetLocation() async {
    state = const AsyncValue.loading();

    final isGpsEnabled = await LocationService.isLocationEnabled();
    if (!isGpsEnabled) {
      state = AsyncValue.data(LocationState(
        isLoading: false,
        isGpsEnabled: false,
        hasPermission: false,
        errorMessage: 'Activa el GPS para usar la app',
      ));
      return;
    }

    final hasPermission = await LocationService.requestPermission();

    if (!hasPermission) {
      state = AsyncValue.data(LocationState(
        isLoading: false,
        isGpsEnabled: true,
        hasPermission: false,
        errorMessage: 'Se necesita permiso de ubicación',
      ));
      return;
    }

    final position = await LocationService.getCurrentPosition();

    if (position != null) {
      state = AsyncValue.data(LocationState(
        isLoading: false,
        isGpsEnabled: true,
        hasPermission: true,
        currentPosition: position,
        currentLatLng: LatLng(position.latitude, position.longitude),
      ));
    }
  }

  /// Centro del mapa para usar cuando no hay ubicación.
  LatLng get mapCenter {
    final currentState = state.valueOrNull;
    if (currentState?.currentLatLng != null) {
      return currentState!.currentLatLng!;
    }
    return LocationService.espinarCenter();
  }
}