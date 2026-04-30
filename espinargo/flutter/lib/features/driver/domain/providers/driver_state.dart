import 'package:google_maps_flutter/google_maps_flutter.dart';

import '../../data/models/driver_profile_model.dart';
import '../../../trips/data/models/trip_model.dart';
import '../../../trips/data/models/trip_offer_model.dart';

/// Estado del flujo del conductor.
enum DriverFlowStatus {
  offline,
  goingOnline,
  online,
  receivedRequest,
  negotiating,
  offerAccepted,
  goingToPassenger,
  passengerOnboard,
  completed,
  error,
}

/// Estado inmutable del conductor.
class DriverState {
  final DriverFlowStatus flowStatus;
  final DriverProfileModel? driverProfile;
  final TripModel? currentTrip;
  final List<Map<String, dynamic>> pendingRequests;
  final TripOfferModel? myOffer;
  final LatLng? passengerLocation;
  final bool isLoading;
  final String? errorMessage;
  final double todayEarnings;
  final int todayTrips;
  final bool isLocationTracking;

  const DriverState({
    this.flowStatus = DriverFlowStatus.offline,
    this.driverProfile,
    this.currentTrip,
    this.pendingRequests = const [],
    this.myOffer,
    this.passengerLocation,
    this.isLoading = false,
    this.errorMessage,
    this.todayEarnings = 0,
    this.todayTrips = 0,
    this.isLocationTracking = false,
  });

  DriverState copyWith({
    DriverFlowStatus? flowStatus,
    DriverProfileModel? driverProfile,
    TripModel? currentTrip,
    List<Map<String, dynamic>>? pendingRequests,
    TripOfferModel? myOffer,
    LatLng? passengerLocation,
    bool? isLoading,
    String? errorMessage,
    double? todayEarnings,
    int? todayTrips,
    bool? isLocationTracking,
  }) {
    return DriverState(
      flowStatus: flowStatus ?? this.flowStatus,
      driverProfile: driverProfile ?? this.driverProfile,
      currentTrip: currentTrip ?? this.currentTrip,
      pendingRequests: pendingRequests ?? this.pendingRequests,
      myOffer: myOffer ?? this.myOffer,
      passengerLocation: passengerLocation ?? this.passengerLocation,
      isLoading: isLoading ?? this.isLoading,
      errorMessage: errorMessage,
      todayEarnings: todayEarnings ?? this.todayEarnings,
      todayTrips: todayTrips ?? this.todayTrips,
      isLocationTracking: isLocationTracking ?? this.isLocationTracking,
    );
  }

  factory DriverState.initial() => const DriverState();
  factory DriverState.online(DriverProfileModel profile) => DriverState(
        flowStatus: DriverFlowStatus.online,
        driverProfile: profile,
      );
  factory DriverState.withRequest(Map<String, dynamic> request) => DriverState(
        flowStatus: DriverFlowStatus.receivedRequest,
        pendingRequests: [request],
      );
  factory DriverState.error(String message) => DriverState(
        flowStatus: DriverFlowStatus.error,
        errorMessage: message,
      );

  bool get isOnline =>
      flowStatus != DriverFlowStatus.offline &&
      flowStatus != DriverFlowStatus.goingOnline;

  bool get hasActiveTrip => currentTrip != null && currentTrip!.isActive;
  bool get hasPendingRequests => pendingRequests.isNotEmpty;
  int get pendingRequestsCount => pendingRequests.length;

  String get statusMessage {
    switch (flowStatus) {
      case DriverFlowStatus.offline:
        return 'Estás desconectado';
      case DriverFlowStatus.goingOnline:
        return 'Conectando...';
      case DriverFlowStatus.online:
        return 'Disponible · Esperando solicitudes';
      case DriverFlowStatus.receivedRequest:
        return 'Nueva solicitud de viaje';
      case DriverFlowStatus.negotiating:
        return 'Oferta enviada';
      case DriverFlowStatus.offerAccepted:
        return '¡Pasajero aceptó tu oferta!';
      case DriverFlowStatus.goingToPassenger:
        return 'En camino al pasajero';
      case DriverFlowStatus.passengerOnboard:
        return 'Viaje en curso';
      case DriverFlowStatus.completed:
        return 'Viaje completado';
      case DriverFlowStatus.error:
        return errorMessage ?? 'Error';
    }
  }
}