import 'dart:async';

import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:google_maps_flutter/google_maps_flutter.dart';

import '../../../../core/network/dio_client.dart';
import '../../../../core/providers.dart';
import '../../data/repositories/driver_repository.dart';
import '../../data/services/driver_websocket_service.dart';
import '../../../trips/data/models/trip_model.dart';
import '../../../trips/data/models/trip_offer_model.dart';
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
      }

      return DriverState.online(profile);
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
      final profile = await repo.setOnlineStatus(false);

      state = AsyncValue.data(currentState!.copyWith(
        flowStatus: DriverFlowStatus.offline,
        driverProfile: profile,
        isLocationTracking: false,
      ));
    } else {
      // Activar
      state = AsyncValue.data(currentState!.copyWith(
        flowStatus: DriverFlowStatus.goingOnline,
      ));

      final repo = ref.read(driverRepositoryProvider);
      final profile = await repo.setOnlineStatus(true);

      await _connectWebSocket();
      await _startLocationTracking();

      state = AsyncValue.data(DriverState.online(profile));
    }
  }

  Future<void> _connectWebSocket() async {
    final wsService = ref.read(driverWebSocketProvider);
    await wsService.connect();

    _subscriptions.add(wsService.onNewTripRequest.listen((data) {
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

    _subscriptions.add(wsService.onTripCancelled.listen((tripId) {
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

    _subscriptions.add(wsService.onOfferAccepted.listen((data) {
      final trip = TripModel.fromJson(data);
      final currentState = state.valueOrNull;
      if (currentState != null) {
        state = AsyncValue.data(currentState.copyWith(
          currentTrip: trip,
          flowStatus: DriverFlowStatus.offerAccepted,
          pendingRequests: [],
        ));
      }
    }));

    _subscriptions.add(wsService.onPassengerLocation.listen((data) {
      final lat = data['lat'] as double;
      final lng = data['lng'] as double;
      final currentState = state.valueOrNull;
      if (currentState != null) {
        state = AsyncValue.data(currentState.copyWith(
          passengerLocation: LatLng(lat, lng),
        ));
      }
    }));
  }

  void _disconnectWebSocket() {
    ref.read(driverWebSocketProvider).disconnect();
  }

  Future<void> _startLocationTracking() async {
    _locationSubscription = LocationService.positionStream().listen((position) {
      final repo = ref.read(driverRepositoryProvider);
      final wsService = ref.read(driverWebSocketProvider);

      repo.updateDriverLocation(lat: position.latitude, lng: position.longitude);
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

      state = AsyncValue.data(currentState.copyWith(
        currentTrip: null,
        myOffer: null,
        flowStatus: DriverFlowStatus.online,
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
        todayEarnings: (earnings['today'] as num?)?.toDouble() ?? 0,
        todayTrips: (earnings['total_trips'] as num?)?.toInt() ?? 0,
      ));
    } catch (_) {}
  }

  /// Resettear estado.
  void resetState() {
    final currentState = state.valueOrNull;
    if (currentState != null) {
      state = AsyncValue.data(currentState.copyWith(
        currentTrip: null,
        myOffer: null,
        passengerLocation: null,
        flowStatus: DriverFlowStatus.online,
      ));
    }
  }

  void _disposeAll() {
    for (final sub in _subscriptions) {
      sub.cancel();
    }
    _subscriptions.clear();
    _locationSubscription?.cancel();
    ref.read(driverWebSocketProvider).dispose();
  }
}