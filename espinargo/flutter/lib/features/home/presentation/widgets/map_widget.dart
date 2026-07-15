import 'package:flutter/material.dart';
import 'package:google_maps_flutter/google_maps_flutter.dart';

import '../../../../core/constants/app_constants.dart';

/// Widget del mapa de Google Maps.
/// Configurado especialmente para EspinarGo.
class MapWidget extends StatefulWidget {
  final Function(GoogleMapController)? onMapCreated;
  final Function(CameraPosition)? onCameraMove;
  final Function()? onCameraIdle;
  final Function(LatLng)? onTap;
  final Set<Marker> markers;
  final Set<Polyline> polylines;
  final LatLng initialPosition;
  final bool showMyLocationButton;

  const MapWidget({
    super.key,
    this.onMapCreated,
    this.onCameraMove,
    this.onCameraIdle,
    this.onTap,
    this.markers = const {},
    this.polylines = const {},
    required this.initialPosition,
    this.showMyLocationButton = false,
  });

  @override
  State<MapWidget> createState() => _MapWidgetState();
}

class _MapWidgetState extends State<MapWidget> {
  GoogleMapController? _controller;

  @override
  Widget build(BuildContext context) {
    return GoogleMap(
      mapType: MapType.normal,
      initialCameraPosition: CameraPosition(
        target: widget.initialPosition,
        zoom: AppConstants.DEFAULT_MAP_ZOOM,
      ),
      onMapCreated: (controller) {
        _controller = controller;
        widget.onMapCreated?.call(controller);
        _applyMapStyle();
      },
      onCameraMove: widget.onCameraMove,
      onCameraIdle: widget.onCameraIdle,
      onTap: widget.onTap,
      myLocationEnabled: true,
      myLocationButtonEnabled: false,
      zoomControlsEnabled: false,
      compassEnabled: false,
      trafficEnabled: false,
      buildingsEnabled: false,
      markers: widget.markers,
      polylines: widget.polylines,
    );
  }

  /// Aplica estilo personalizado al mapa para reducir ruido visual.
  void _applyMapStyle() {
    if (_controller == null) return;

    // Estilo JSON para el mapa - tonos suaves con marcadores destacados
    const String mapStyle = '''
[
  {
    "featureType": "poi",
    "elementType": "labels",
    "stylers": [{"visibility": "off"}]
  },
  {
    "featureType": "transit",
    "elementType": "labels",
    "stylers": [{"visibility": "off"}]
  },
  {
    "featureType": "water",
    "elementType": "geometry.fill",
    "stylers": [{"color": "#c8e6c9"}]
  },
  {
    "featureType": "road",
    "elementType": "geometry",
    "stylers": [{"color": "#ffffff"}]
  }
]
''';
    _controller?.setMapStyle(mapStyle);
  }

  /// Animación de la cámara para mostrar la ruta completa.
  Future<void> animateToRoute(LatLngBounds bounds) async {
    await _controller?.animateCamera(
      CameraUpdate.newLatLngBounds(bounds, 80),
    );
  }

  /// Centra el mapa en una posición específica.
  Future<void> animateToPosition(LatLng position, {double? zoom}) async {
    if (zoom != null) {
      await _controller?.animateCamera(
        CameraUpdate.newCameraPosition(
          CameraPosition(target: position, zoom: zoom),
        ),
      );
    } else {
      await _controller?.animateCamera(
        CameraUpdate.newLatLng(position),
      );
    }
  }
}