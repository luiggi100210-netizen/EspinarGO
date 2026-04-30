import 'dart:async';

import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:google_maps_flutter/google_maps_flutter.dart';

import '../../../../core/network/dio_client.dart';
import '../../../../core/providers.dart';
import '../../data/models/trip_model.dart';
import '../../data/models/trip_offer_model.dart';
import '../../data/repositories/trip_repository.dart';
import '../../data/services/trip_websocket_service.dart';
import 'trip_state.dart';

/// Provider del repositorio de viajes.
final tripRepositoryProvider = Provider<TripRepository>((ref) {
  final dioClient = ref.watch(dioClientProvider);
  return TripRepository(dioClient: dioClient);
});

/// Provider del servicio WebSocket.
final tripWebSocketProvider = Provider<TripWebSocketService>((ref) {
  return TripWebSocketService();
});

/// Provider principal de viajes.
final tripProvider = AsyncNotifierProvider<TripNotifier, TripState>(() {
  return TripNotifier();
});

/// Notificador de viajes.
/// Conecta la UI con el repositorio y el WebSocket.
class TripNotifier extends AsyncNotifier<TripState> {
  final List<StreamSubscription> _subscriptions = [];

  @override
  Future<TripState> build() async {
    ref.onDispose(() {
      _disposeAll();
    });
    return _checkActiveTrip();
  }

  /// Verifica si hay un viaje activo.
  Future<TripState> _checkActiveTrip() async {
    final repository = ref.read(tripRepositoryProvider);

    try {
      final trip = await repository.getActiveTrip();

      if (trip != null && trip.isActive) {
        // Conectar WebSocket para actualizaciones en tiempo real
        await _connectWebSocket(trip.id);

        return _mapTripStatusToFlowStatus(trip);
      }

      return const TripState();
    } catch (e) {
      return const TripState();
    }
  }

  /// Mapea el status del viaje al estado del flujo.
  TripState _mapTripStatusToFlowStatus(TripModel trip) {
    switch (trip.status) {
      case 'searching':
      case 'negotiating':
        return TripState.searching(trip);
      case 'accepted':
        return TripState(
          flowStatus: TripFlowStatus.accepted,
          currentTrip: trip,
        );
      case 'in_progress':
        return TripState(
          flowStatus: TripFlowStatus.inProgress,
          currentTrip: trip,
        );
      case 'completed':
        return TripState(
          flowStatus: TripFlowStatus.completed,
          currentTrip: trip,
        );
      default:
        return TripState.searching(trip);
    }
  }

  /// Crea un nuevo viaje.
  Future<bool> createTrip({
    required String originAddress,
    required double originLat,
    required double originLng,
    required String destAddress,
    required double destLat,
    required double destLng,
    required String proposedPrice,
    String paymentMethod = 'cash',
  }) async {
    state = const AsyncValue.loading();

    try {
      final repository = ref.read(tripRepositoryProvider);
      final trip = await repository.createTrip(
        originAddress: originAddress,
        originLat: originLat,
        originLng: originLng,
        destAddress: destAddress,
        destLat: destLat,
        destLng: destLng,
        proposedPrice: proposedPrice,
        paymentMethod: paymentMethod,
      );

      state = AsyncValue.data(TripState.searching(trip));

      // Conectar WebSocket
      await _connectWebSocket(trip.id);

      return true;
    } catch (e) {
      state = AsyncValue.error(e.toString(), StackTrace.current);
      return false;
    }
  }

  /// Conecta al WebSocket y escucha eventos.
  Future<void> _connectWebSocket(String tripId) async {
    final wsService = ref.read(tripWebSocketProvider);

    await wsService.connect(tripId);

    // Escuchar nuevas ofertas
    _subscriptions.add(wsService.onNewOffer.listen((data) {
      final offer = TripOfferModel.fromJson(data);
      final currentState = state.valueOrNull;
      if (currentState != null) {
        final updatedOffers = [...currentState.offers, offer];
        state = AsyncValue.data(currentState.copyWith(
          offers: updatedOffers,
          flowStatus: TripFlowStatus.hasOffers,
        ));
      }
    }));

    // Escuchar actualizaciones del viaje
    _subscriptions.add(wsService.onTripUpdated.listen((data) {
      final trip = TripModel.fromJson(data);
      final currentState = state.valueOrNull;
      if (currentState != null) {
        state = AsyncValue.data(currentState.copyWith(
          currentTrip: trip,
          flowStatus: _mapTripStatusToFlowStatus(trip).flowStatus,
        ));
      }
    }));

    // Escuchar ubicación del conductor
    _subscriptions.add(wsService.onDriverLocation.listen((data) {
      final lat = data['lat'] as double;
      final lng = data['lng'] as double;
      final currentState = state.valueOrNull;
      if (currentState != null) {
        state = AsyncValue.data(currentState.copyWith(
          driverLocation: LatLng(lat, lng),
        ));
      }
    }));

    // Conductor llegó
    _subscriptions.add(wsService.onDriverArrived.listen((_) {
      final currentState = state.valueOrNull;
      if (currentState != null) {
        state = AsyncValue.data(currentState.copyWith(
          flowStatus: TripFlowStatus.driverArrived,
        ));
      }
    }));

    // Viaje iniciado
    _subscriptions.add(wsService.onTripStarted.listen((_) {
      final currentState = state.valueOrNull;
      if (currentState != null) {
        state = AsyncValue.data(currentState.copyWith(
          flowStatus: TripFlowStatus.inProgress,
        ));
      }
    }));

    // Viaje completado
    _subscriptions.add(wsService.onTripCompleted.listen((_) {
      final currentState = state.valueOrNull;
      if (currentState != null) {
        state = AsyncValue.data(currentState.copyWith(
          flowStatus: TripFlowStatus.completed,
        ));
      }
    }));
  }

  /// Obtiene las ofertas de un viaje.
  Future<void> getOffers(String tripId) async {
    final repository = ref.read(tripRepositoryProvider);
    final currentState = state.valueOrNull;

    try {
      final offers = await repository.getTripOffers(tripId);
      if (currentState != null) {
        state = AsyncValue.data(currentState.copyWith(
          offers: offers,
          flowStatus: offers.isNotEmpty
              ? TripFlowStatus.hasOffers
              : TripFlowStatus.searching,
        ));
      }
    } catch (e) {
      if (currentState != null) {
        state = AsyncValue.data(currentState.copyWith(
          errorMessage: e.toString(),
        ));
      }
    }
  }

  /// Acepta una oferta.
  Future<bool> acceptOffer(String offerId) async {
    final currentState = state.valueOrNull;
    if (currentState == null || currentState.currentTrip == null) {
      return false;
    }

    state = const AsyncValue.loading();

    try {
      final repository = ref.read(tripRepositoryProvider);
      final trip = await repository.acceptOffer(
        tripId: currentState.currentTrip!.id,
        offerId: offerId,
      );

      final selectedOffer = currentState.offers.firstWhere(
        (o) => o.id == offerId,
      );

      state = AsyncValue.data(currentState.copyWith(
        currentTrip: trip,
        selectedOffer: selectedOffer,
        flowStatus: TripFlowStatus.accepted,
      ));

      return true;
    } catch (e) {
      state = AsyncValue.data(currentState);
      return false;
    }
  }

  /// Cancela el viaje actual.
  Future<bool> cancelTrip() async {
    final currentState = state.valueOrNull;
    if (currentState?.currentTrip == null) return false;

    try {
      final repository = ref.read(tripRepositoryProvider);
      await repository.cancelTrip(currentState!.currentTrip!.id);

      _disposeAll();

      state = const AsyncValue.data(TripState());
      return true;
    } catch (e) {
      return false;
    }
  }

  /// Carga el historial de viajes.
  Future<void> loadTripHistory() async {
    final currentState = state.valueOrNull;
    if (currentState == null) return;

    state = AsyncValue.data(currentState.copyWith(isLoadingHistory: true));

    try {
      final repository = ref.read(tripRepositoryProvider);
      final history = await repository.getTripHistory();

      state = AsyncValue.data(currentState.copyWith(
        tripHistory: history,
        isLoadingHistory: false,
      ));
    } catch (e) {
      state = AsyncValue.data(currentState.copyWith(isLoadingHistory: false));
    }
  }

  /// Limpia el error del estado.
  void clearError() {
    final currentState = state.valueOrNull;
    if (currentState != null) {
      state = AsyncValue.data(currentState.copyWith(errorMessage: null));
    }
  }

  /// Resetea el estado del viaje.
  void resetTrip() {
    _disposeAll();
    state = const AsyncValue.data(TripState());
  }

  /// Libera todos los recursos.
  void _disposeAll() {
    for (final sub in _subscriptions) {
      sub.cancel();
    }
    _subscriptions.clear();
    ref.read(tripWebSocketProvider).dispose();
  }
}