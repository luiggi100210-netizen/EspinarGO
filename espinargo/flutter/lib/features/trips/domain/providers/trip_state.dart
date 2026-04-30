import 'package:google_maps_flutter/google_maps_flutter.dart';

import '../../data/models/trip_model.dart';
import '../../data/models/trip_offer_model.dart';

/// Estado del flujo de viajes.
enum TripFlowStatus {
  idle,
  creating,
  searching,
  hasOffers,
  accepted,
  driverEnRoute,
  driverArrived,
  inProgress,
  completed,
  cancelled,
  error,
}

/// Estado inmutable del módulo de viajes.
class TripState {
  final TripFlowStatus flowStatus;
  final TripModel? currentTrip;
  final List<TripOfferModel> offers;
  final TripOfferModel? selectedOffer;
  final LatLng? driverLocation;
  final bool isLoading;
  final String? errorMessage;
  final List<TripModel> tripHistory;
  final bool isLoadingHistory;

  const TripState({
    this.flowStatus = TripFlowStatus.idle,
    this.currentTrip,
    this.offers = const [],
    this.selectedOffer,
    this.driverLocation,
    this.isLoading = false,
    this.errorMessage,
    this.tripHistory = const [],
    this.isLoadingHistory = false,
  });

  TripState copyWith({
    TripFlowStatus? flowStatus,
    TripModel? currentTrip,
    List<TripOfferModel>? offers,
    TripOfferModel? selectedOffer,
    LatLng? driverLocation,
    bool? isLoading,
    String? errorMessage,
    List<TripModel>? tripHistory,
    bool? isLoadingHistory,
  }) {
    return TripState(
      flowStatus: flowStatus ?? this.flowStatus,
      currentTrip: currentTrip ?? this.currentTrip,
      offers: offers ?? this.offers,
      selectedOffer: selectedOffer ?? this.selectedOffer,
      driverLocation: driverLocation ?? this.driverLocation,
      isLoading: isLoading ?? this.isLoading,
      errorMessage: errorMessage,
      tripHistory: tripHistory ?? this.tripHistory,
      isLoadingHistory: isLoadingHistory ?? this.isLoadingHistory,
    );
  }

  /// factories
  factory TripState.initial() => const TripState(isLoading: true);

  factory TripState.loading() => const TripState(isLoading: true);

  factory TripState.searching(TripModel trip) => TripState(
        flowStatus: TripFlowStatus.searching,
        currentTrip: trip,
        isLoading: false,
      );

  factory TripState.hasOffers(TripModel trip, List<TripOfferModel> offers) =>
      TripState(
        flowStatus: TripFlowStatus.hasOffers,
        currentTrip: trip,
        offers: offers,
        isLoading: false,
      );

  factory TripState.error(String message) => TripState(
        flowStatus: TripFlowStatus.error,
        errorMessage: message,
        isLoading: false,
      );

  /// Getters
  bool get hasActiveTrip =>
      currentTrip != null && currentTrip!.isActive;

  bool get canAcceptOffers =>
      flowStatus == TripFlowStatus.hasOffers;

  int get offersCount => offers.length;

  /// Mensaje según el estado del flujo.
  String get statusMessage {
    switch (flowStatus) {
      case TripFlowStatus.idle:
        return '¿A dónde vas hoy?';
      case TripFlowStatus.creating:
        return 'Creando solicitud...';
      case TripFlowStatus.searching:
        return 'Buscando conductores cerca de ti...';
      case TripFlowStatus.hasOffers:
        return '¡Tienes $offersCount oferta(s)!';
      case TripFlowStatus.accepted:
        return 'Conductor en camino';
      case TripFlowStatus.driverEnRoute:
        return 'Conductor en camino';
      case TripFlowStatus.driverArrived:
        return '¡Tu conductor llegó!';
      case TripFlowStatus.inProgress:
        return 'Viaje en curso';
      case TripFlowStatus.completed:
        return '¡Llegaste a tu destino!';
      case TripFlowStatus.cancelled:
        return 'Viaje cancelado';
      case TripFlowStatus.error:
        return errorMessage ?? 'Error en el viaje';
    }
  }
}