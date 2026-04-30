import 'dart:convert';

import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import 'package:google_maps_flutter/google_maps_flutter.dart';

import '../../../../core/theme/app_colors.dart';
import '../../../../core/theme/app_text_styles.dart';
import '../../../../shared/widgets/app_drawer.dart';
import '../../../auth/domain/providers/auth_provider.dart';
import '../../data/models/place_model.dart';
import '../../domain/providers/location_provider.dart';
import '../../domain/providers/map_provider.dart';
import '../widgets/bottom_sheet_home.dart';
import '../widgets/driver_marker.dart';
import '../widgets/map_widget.dart';
import '../widgets/my_location_button.dart';
import '../widgets/search_bar_widget.dart';
import 'search_destination_screen.dart';

/// Pantalla principal de la app para el pasajero.
/// Combina el mapa, barra de búsqueda, panel inferior y marcadores.
class HomeScreen extends ConsumerStatefulWidget {
  const HomeScreen({super.key});

  @override
  ConsumerState<HomeScreen> createState() => _HomeScreenState();
}

class _HomeScreenState extends ConsumerState<HomeScreen> {
  final GlobalKey<ScaffoldState> _scaffoldKey = GlobalKey<ScaffoldState>();
  GoogleMapController? _mapController;

  @override
  Widget build(BuildContext context) {
    final locationState = ref.watch(locationProvider).valueOrNull;
    final mapState = ref.watch(mapProvider).valueOrNull;
    final authState = ref.watch(authProvider).valueOrNull;

    // Posición inicial del mapa
    final initialPosition = locationState?.currentLatLng ??
        ref.read(locationProvider.notifier).mapCenter;

    // Crear marcadores
    final markers = _buildMarkers(mapState, locationState);

    // Crear polilíneas
    final polylines = _buildPolylines(mapState);

    return Scaffold(
      key: _scaffoldKey,
      drawer: authState?.user != null
          ? AppDrawer(
              user: authState!.user!,
              onLogout: () => _handleLogout(),
            )
          : null,
      body: Stack(
        children: [
          // Capa 1: Mapa
          MapWidget(
            initialPosition: initialPosition,
            onMapCreated: (controller) {
              _mapController = controller;
            },
            markers: markers,
            polylines: polylines,
            onCameraIdle: () => _onCameraIdle(),
          ),

          // Capa 2: Panel superior
          SafeArea(
            child: Padding(
              padding: const EdgeInsets.all(16),
              child: Row(
                children: [
                  // Avatar
                  GestureDetector(
                    onTap: () => _scaffoldKey.currentState?.openDrawer(),
                    child: Container(
                      width: 44,
                      height: 44,
                      decoration: BoxDecoration(
                        color: AppColors.primary,
                        shape: BoxShape.circle,
                      ),
                      child: Center(
                        child: Text(
                          authState?.user?.initials ?? '?',
                          style: AppTextStyles.labelLarge.copyWith(
                            color: Colors.white,
                          ),
                        ),
                      ),
                    ),
                  ),
                  const SizedBox(width: 12),
                  // Barra de búsqueda
                  Expanded(
                    child: SearchBarWidget(
                      onTap: _navigateToSearch,
                      currentOriginName: mapState?.origin?.name,
                    ),
                  ),
                ],
              ),
            ),
          ),

          // Capa 3: Botón de mi ubicación
          Positioned(
            right: 16,
            bottom: mapState?.route != null ? 300 : 200,
            child: MyLocationButton(
              onPressed: _centerOnMyLocation,
              isLoading: locationState?.isLoading ?? false,
            ),
          ),

          // Capa 4: Panel inferior
          Positioned(
            left: 0,
            right: 0,
            bottom: 0,
            child: BottomSheetHome(
              mapState: mapState ?? const MapState(),
              onRequestTrip: _onRequestTrip,
              onClearRoute: () => ref.read(mapProvider.notifier).clearRoute(),
            ),
          ),
        ],
      ),
    );
  }

  /// Construye los marcadores del mapa.
  Set<Marker> _buildMarkers(MapState? mapState, LocationState? locationState) {
    final markers = <Marker>{};

    // Marcador de origen si hay ruta
    if (mapState?.origin != null) {
      markers.add(createOriginMarker(mapState!.origin!.toLatLng()));
    }

    // Marcador de destino si hay ruta
    if (mapState?.destination != null) {
      markers.add(createDestinationMarker(mapState!.destination!.toLatLng()));
    }

    // Marcador de posición actual del usuario
    if (locationState?.currentLatLng != null) {
      markers.add(createOriginMarker(locationState!.currentLatLng!));
    }

    // Conductores cercanos simulados (en M4 se conecta con WebSocket)
    if (mapState?.nearbyDrivers.isNotEmpty ?? false) {
      for (final driver in mapState!.nearbyDrivers) {
        markers.add(DriverMarker.create(
          driverId: driver.placeId,
          position: driver.toLatLng(),
          vehicleType: mapState.selectedService,
          isOnline: true,
        ));
      }
    }

    return markers;
  }

  /// Construye las polilíneas de la ruta.
  Set<Polyline> _buildPolylines(MapState? mapState) {
    if (mapState?.route == null) return {};

    return {
      Polyline(
        polylineId: const PolylineId('route'),
        points: mapState!.route!.polylinePoints,
        color: AppColors.info,
        width: 5,
      ),
    };
  }

  /// Navega a la pantalla de búsqueda de destino.
  Future<void> _navigateToSearch() async {
    final locationState = ref.read(locationProvider).valueOrNull;

    // Guardar origen como la ubicación actual
    if (locationState?.currentLatLng != null) {
      final originPlace = PlaceModel(
        placeId: 'current_location',
        name: 'Mi ubicación',
        address: '',
        lat: locationState!.currentLatLng!.latitude,
        lng: locationState.currentLatLng!.longitude,
      );
      await ref.read(mapProvider.notifier).setOrigin(originPlace);
    }

    // Navegar a la pantalla de búsqueda
    final result = await Navigator.push<PlaceModel>(
      context,
      MaterialPageRoute(builder: (_) => const SearchDestinationScreen()),
    );

    if (result != null) {
      // La selección ya se maneja en el provider
    }
  }

  /// Centra el mapa en la ubicación actual.
  Future<void> _centerOnMyLocation() async {
    final locationState = ref.read(locationProvider).valueOrNull;

    if (locationState?.currentLatLng != null) {
      await _mapController?.animateCamera(
        CameraUpdate.newLatLng(locationState!.currentLatLng!),
      );
    } else {
      // Solicitar ubicación
      await ref.read(locationProvider.notifier).requestPermissionAndGetLocation();
    }
  }

  /// Callback cuando la cámara del mapa se detiene.
  void _onCameraIdle() {
    // Aquí se puede hacer reverse geocoding si es necesario
  }

  /// Callback cuando se presiona el botón de solicitar viaje.
  void _onRequestTrip() {
    final mapState = ref.read(mapProvider).valueOrNull;
    final route = mapState?.route;
    if (route == null) return;

    final routeJson = jsonEncode({
      'origin_place_id': route.origin.placeId,
      'origin_name': route.origin.name,
      'origin_address': route.origin.address,
      'origin_lat': route.origin.lat,
      'origin_lng': route.origin.lng,
      'dest_place_id': route.destination.placeId,
      'dest_name': route.destination.name,
      'dest_address': route.destination.address,
      'dest_lat': route.destination.lat,
      'dest_lng': route.destination.lng,
      'distance_km': route.distanceKm,
      'duration_minutes': route.durationMinutes,
      'suggested_price': route.suggestedPrice,
      'min_price': route.minPrice,
      'max_price': route.maxPrice,
    });

    context.push(
      Uri(
        path: '/propose-price',
        queryParameters: {'routeJson': routeJson},
      ).toString(),
    );
  }

  /// Maneja el cierre de sesión.
  Future<void> _handleLogout() async {
    await ref.read(authProvider.notifier).logout();
    if (mounted) {
      context.go('/login');
    }
  }
}