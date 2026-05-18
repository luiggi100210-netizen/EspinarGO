import 'dart:async';

import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../../../core/providers.dart';
import '../../data/repositories/driver_repository.dart';
import '../../data/services/driver_websocket_service.dart';
import '../../../home/data/services/location_service.dart';
import 'driver_state.dart';

/// Provider del repositorio del conductor.
final driverRepositoryProvider = Provider<DriverRepository>((ref) {
  final dioClient = ref.watch(dioClientProvider);
  return DriverRepository(dioClient: dioClient);
});

/// Provider del WebSocket del conductor.
final driverWebSocketProvider = Provider<DriverWebSocketService>((ref) {
  return DriverWebSocketService();
});

/// Provider principal del conductor.
final driverProvider = AsyncNotifierProvider<DriverNotifier, DriverState>(() {
  return DriverNotifier();
});

/// Notificador del conductor.
class DriverNotifier extends AsyncNotifier<DriverState> {
  final List<StreamSubscription> _subscriptions = [];
  StreamSubscription<dynamic>? _locationSubscription;
  DriverWebSocketService? _wsService;

  @override
  Future<DriverState> build() async {
    ref.onDispose(() => _disposeAll());
    return _loadDriverProfile();
  }

  Future<DriverState> _loadDriverProfile() async {
    try {
      final repo = ref.read(driverRepositoryProvider);
      final profile = await repo.getMyDriverProfile();

      if (profile.isOnline) {
        await _connectWebSocket();
        return DriverState.online(profile);
      }

      return DriverState(
        flowStatus: DriverFlowStatus.offline,
        driverProfile: profile,
      );
    } catch (e) {
      return const DriverState();
    }
  }

  /// Activar o desactivar modo online.
  Future<void> toggleOnline() async {
    final currentState = state.valueOrNull;
    final isCurrentlyOnline = currentState?.isOnline ?? false;

    if (isCurrentlyOnline) {
      // Desactivar
      await _stopLocationTracking();
      _disconnectWebSocket();

      final repo = ref.read(driverRepositoryProvider);
      await repo.setOnlineStatus(false);

      state = AsyncValue.data(currentState!.copyWith(
        flowStatus: DriverFlowStatus.offline,
        isLocationTracking: false,
      ));
    } else {
      // Activar
      state = AsyncValue.data(currentState!.copyWith(
        flowStatus: DriverFlowStatus.goingOnline,
      ));

      final repo = ref.read(driverRepositoryProvider);
      await repo.setOnlineStatus(true);

      await _connectWebSocket();
      await _startLocationTracking();

      state = AsyncValue.data(currentState.copyWith(
        flowStatus: DriverFlowStatus.online,
      ));
    }
  }

  Future<void> _connectWebSocket() async {
    _wsService = ref.read(driverWebSocketProvider);
    await _wsService!.connect();

    _subscriptions.add(_wsService!.onNewTripRequest.listen((data) {
      final currentState = state.valueOrNull;
      if (currentState != null) {
        final requests = [...currentState.pendingRequests, data];
        state = AsyncValue.data(currentState.copyWith(
          pendingRequests: requests,
          flowStatus: requests.length == 1
              ? DriverFlowStatus.receivedRequest
              : DriverFlowStatus.online,
        ));
      }
    }));

    _subscriptions.add(_wsService!.onTripCancelled.listen((tripId) {
      final currentState = state.valueOrNull;
      if (currentState != null) {
        final requests = currentState.pendingRequests
            .where((r) => r['trip_id'] != tripId)
            .toList();
        state = AsyncValue.data(currentState.copyWith(
          pendingRequests: requests,
          flowStatus: requests.isEmpty
              ? DriverFlowStatus.online
              : DriverFlowStatus.receivedRequest,
        ));
      }
    }));

    _subscriptions.add(_wsService!.onOfferAccepted.listen((data) async {
      final currentState = state.valueOrNull;
      if (currentState == null) return;
      // Marcar estado inmediatamente, luego cargar viaje completo via REST
      state = AsyncValue.data(currentState.copyWith(
        flowStatus: DriverFlowStatus.offerAccepted,
        pendingRequests: [],
      ));
      try {
        final repo = ref.read(driverRepositoryProvider);
        final trip = await repo.getDriverActiveTrip();
        final updatedState = state.valueOrNull;
        if (trip != null && updatedState != null) {
          state = AsyncValue.data(updatedState.copyWith(currentTrip: trip));
        }
      } catch (_) {}
    }));
  }

  void _disconnectWebSocket() {
    _wsService?.disconnect();
  }

  Future<void> _startLocationTracking() async {
    _locationSubscription = LocationService.positionStream().listen((position) {
      final wsService = ref.read(driverWebSocketProvider);
      wsService.updateLocation(position.latitude, position.longitude);

      final currentState = state.valueOrNull;
      if (currentState != null) {
        state = AsyncValue.data(currentState.copyWith(isLocationTracking: true));
      }
    });
  }

  Future<void> _stopLocationTracking() async {
    await _locationSubscription?.cancel();
    _locationSubscription = null;
  }

  /// Hacer oferta a un viaje.
  Future<bool> makeOffer({
    required String tripId,
    required String price,
    String? message,
  }) async {
    final currentState = state.valueOrNull;
    if (currentState == null) return false;

    try {
      final repo = ref.read(driverRepositoryProvider);
      final offer = await repo.makeOffer(
        tripId: tripId,
        offeredPrice: price,
        message: message,
      );

      state = AsyncValue.data(currentState.copyWith(
        myOffer: offer,
        flowStatus: DriverFlowStatus.negotiating,
      ));
      return true;
    } catch (e) {
      return false;
    }
  }

  /// Ignorar una solicitud.
  void rejectRequest(String tripId) {
    final currentState = state.valueOrNull;
    if (currentState == null) return;

    final requests = currentState.pendingRequests
        .where((r) => r['trip_id'] != tripId)
        .toList();

    state = AsyncValue.data(currentState.copyWith(
      pendingRequests: requests,
      flowStatus: requests.isEmpty
          ? DriverFlowStatus.online
          : DriverFlowStatus.receivedRequest,
    ));
  }

  /// Iniciar viaje (pasajero a bordo).
  Future<bool> startTrip(String tripId) async {
    final currentState = state.valueOrNull;
    if (currentState == null) return false;

    try {
      final repo = ref.read(driverRepositoryProvider);
      final trip = await repo.startTrip(tripId);

      state = AsyncValue.data(currentState.copyWith(
        currentTrip: trip,
        flowStatus: DriverFlowStatus.passengerOnboard,
      ));
      return true;
    } catch (e) {
      return false;
    }
  }

  /// Completar viaje.
  Future<bool> completeTrip(String tripId) async {
    final currentState = state.valueOrNull;
    if (currentState == null) return false;

    try {
      final repo = ref.read(driverRepositoryProvider);
      final trip = await repo.completeTrip(tripId);

      state = AsyncValue.data(currentState.copyWith(
        currentTrip: trip,
        flowStatus: DriverFlowStatus.completed,
        todayTrips: currentState.todayTrips + 1,
        todayEarnings: currentState.todayEarnings +
            (double.tryParse(trip.finalPrice ?? trip.proposedPrice) ?? 0),
      ));
      return true;
    } catch (e) {
      return false;
    }
  }

  /// Cancelar viaje.
  Future<bool> cancelTrip(String tripId) async {
    final currentState = state.valueOrNull;
    if (currentState == null) return false;

    try {
      final repo = ref.read(driverRepositoryProvider);
      await repo.cancelTrip(tripId);

      state = AsyncValue.data(DriverState(
        flowStatus: DriverFlowStatus.online,
        driverProfile: currentState.driverProfile,
        pendingRequests: const [],
        todayEarnings: currentState.todayEarnings,
        todayTrips: currentState.todayTrips,
        isLocationTracking: currentState.isLocationTracking,
      ));
      return true;
    } catch (e) {
      return false;
    }
  }

  /// Cargar ganancias.
  Future<void> loadEarnings() async {
    final currentState = state.valueOrNull;
    if (currentState == null) return;

    try {
      final repo = ref.read(driverRepositoryProvider);
      final earnings = await repo.getDriverEarnings();

      state = AsyncValue.data(currentState.copyWith(
        todayEarnings: double.tryParse(earnings['this_week_earnings'] as String? ?? '0') ?? 0,
        todayTrips: (earnings['total_trips'] as num?)?.toInt() ?? 0,
      ));
    } catch (_) {}
  }

  /// Resettear estado.
  void resetState() {
    final currentState = state.valueOrNull;
    if (currentState != null) {
      state = AsyncValue.data(DriverState(
        flowStatus: DriverFlowStatus.online,
        driverProfile: currentState.driverProfile,
        todayEarnings: currentState.todayEarnings,
        todayTrips: currentState.todayTrips,
        isLocationTracking: currentState.isLocationTracking,
      ));
    }
  }

  void _disposeAll() {
    for (final sub in _subscriptions) {
      sub.cancel();
    }
    _subscriptions.clear();
    _locationSubscription?.cancel();
    _wsService?.dispose();
    _wsService = null;
  }
}