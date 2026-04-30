import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:google_maps_flutter/google_maps_flutter.dart';

import '../../../../core/network/dio_client.dart';
import '../../../../core/providers.dart';
import '../../data/models/place_model.dart';
import '../../data/models/route_model.dart';
import '../../data/services/maps_service.dart';

/// Modo del mapa en la pantalla principal.
enum MapMode {
  /// Mapa en reposo, mostrando la posición actual.
  idle,

  /// El usuario está moviendo el mapa para elegir origen.
  selectingOrigin,

  /// Buscando destino.
  searchingDestination,

  /// Origen y destino seleccionados, ruta calculada.
  routeSelected,

  /// Esperando respuesta de solicitud de viaje.
  waiting,
}

/// Estado del mapa y búsqueda de destino.
class MapState {
  final MapMode mode;
  final PlaceModel? origin;
  final PlaceModel? destination;
  final RouteModel? route;
  final List<PlaceModel> searchResults;
  final bool isLoadingRoute;
  final bool isSearching;
  final String selectedService;
  final List<PlaceModel> nearbyDrivers;

  const MapState({
    this.mode = MapMode.idle,
    this.origin,
    this.destination,
    this.route,
    this.searchResults = const [],
    this.isLoadingRoute = false,
    this.isSearching = false,
    this.selectedService = 'mototaxi',
    this.nearbyDrivers = const [],
  });

  MapState copyWith({
    MapMode? mode,
    PlaceModel? origin,
    PlaceModel? destination,
    RouteModel? route,
    List<PlaceModel>? searchResults,
    bool? isLoadingRoute,
    bool? isSearching,
    String? selectedService,
    List<PlaceModel>? nearbyDrivers,
  }) {
    return MapState(
      mode: mode ?? this.mode,
      origin: origin ?? this.origin,
      destination: destination ?? this.destination,
      route: route ?? this.route,
      searchResults: searchResults ?? this.searchResults,
      isLoadingRoute: isLoadingRoute ?? this.isLoadingRoute,
      isSearching: isSearching ?? this.isSearching,
      selectedService: selectedService ?? this.selectedService,
      nearbyDrivers: nearbyDrivers ?? this.nearbyDrivers,
    );
  }
}

/// Provider del servicio de mapas.
final mapsServiceProvider = Provider<MapsService>((ref) {
  final dioClient = ref.watch(dioClientProvider);
  return MapsService(dioClient: dioClient);
});

/// Provider del estado del mapa.
final mapProvider = AsyncNotifierProvider<MapNotifier, MapState>(() {
  return MapNotifier();
});

/// Notificador del estado del mapa.
/// Controla marcadores, rutas y modo del mapa.
class MapNotifier extends AsyncNotifier<MapState> {
  @override
  Future<MapState> build() async {
    return const MapState();
  }

  /// Establece el origen del viaje.
  Future<void> setOrigin(PlaceModel place) async {
    final currentState = state.valueOrNull ?? const MapState();
    state = AsyncValue.data(currentState.copyWith(
      origin: place,
      mode: currentState.destination != null ? MapMode.routeSelected : MapMode.idle,
    ));

    // Si hay destino, calcular ruta
    if (currentState.destination != null) {
      await _calculateRoute();
    }
  }

  /// Establece el destino del viaje.
  Future<void> setDestination(PlaceModel place) async {
    final currentState = state.valueOrNull ?? const MapState();
    state = AsyncValue.data(currentState.copyWith(
      destination: place,
      mode: MapMode.searchingDestination,
    ));

    // Calcular ruta si hay origen
    if (currentState.origin != null) {
      await _calculateRoute();
    }
  }

  /// Calcula la ruta entre origen y destino.
  Future<void> _calculateRoute() async {
    final currentState = state.valueOrNull;
    if (currentState == null) return;

    state = AsyncValue.data(currentState.copyWith(isLoadingRoute: true));

    final mapsService = ref.read(mapsServiceProvider);
    final route = await mapsService.getRoute(
      currentState.origin!.toLatLng(),
      currentState.destination!.toLatLng(),
    );

    if (route != null) {
      state = AsyncValue.data(currentState.copyWith(
        route: route,
        mode: MapMode.routeSelected,
        isLoadingRoute: false,
      ));
    } else {
      state = AsyncValue.data(currentState.copyWith(isLoadingRoute: false));
    }
  }

  /// Busca lugares según el query.
  Future<void> searchPlaces(String query, {LatLng? userLocation}) async {
    final currentState = state.valueOrNull ?? const MapState();

    if (query.isEmpty) {
      state = AsyncValue.data(currentState.copyWith(
        searchResults: [],
        isSearching: false,
      ));
      return;
    }

    state = AsyncValue.data(currentState.copyWith(isSearching: true));

    final mapsService = ref.read(mapsServiceProvider);
    final results = await mapsService.searchPlaces(query, userLocation: userLocation);

    state = AsyncValue.data(currentState.copyWith(
      searchResults: results,
      isSearching: false,
    ));
  }

  /// Limpia la búsqueda de destinos.
  void clearSearch() {
    final currentState = state.valueOrNull ?? const MapState();
    state = AsyncValue.data(currentState.copyWith(
      searchResults: [],
      mode: currentState.origin != null ? MapMode.idle : MapMode.searchingDestination,
    ));
  }

  /// Selecciona el tipo de servicio.
  void setSelectedService(String service) {
    final currentState = state.valueOrNull ?? const MapState();
    state = AsyncValue.data(currentState.copyWith(selectedService: service));
  }

  /// Cambia el modo del mapa.
  void setMapMode(MapMode mode) {
    final currentState = state.valueOrNull ?? const MapState();
    state = AsyncValue.data(currentState.copyWith(mode: mode));
  }

  /// Limpia la ruta y vuelve al modo idle.
  void clearRoute() {
    final currentState = state.valueOrNull ?? const MapState();
    state = AsyncValue.data(currentState.copyWith(
      origin: null,
      destination: null,
      route: null,
      mode: MapMode.idle,
    ));
  }

  /// Actualiza los conductores cercanos.
  void updateNearbyDrivers(List<PlaceModel> drivers) {
    final currentState = state.valueOrNull ?? const MapState();
    state = AsyncValue.data(currentState.copyWith(nearbyDrivers: drivers));
  }
}