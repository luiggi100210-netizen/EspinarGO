import 'dart:ui' show Offset;

import 'package:google_maps_flutter/google_maps_flutter.dart';

/// Genera marcadores personalizados para los conductores.
class DriverMarker {
  /// Crea un marcador de conductor en el mapa.
  static Marker create({
    required String driverId,
    required LatLng position,
    required String vehicleType,
    bool isOnline = true,
  }) {
    final emoji = vehicleType == 'mototaxi' ? '🛺' : '🚗';

    return Marker(
      markerId: MarkerId(driverId),
      position: position,
      icon: BitmapDescriptor.defaultMarkerWithHue(
        isOnline ? BitmapDescriptor.hueOrange : BitmapDescriptor.hueOrange,
      ),
      zIndex: 1.0,
      infoWindow: InfoWindow(
        title: emoji,
        snippet: isOnline ? 'Disponible' : 'Desconectado',
      ),
    );
  }

  /// Crea un marcador de conductor con bitmap custom.
  static Future<Marker> createCustom({
    required String driverId,
    required LatLng position,
    required String vehicleType,
    bool isOnline = true,
  }) async {
    final emoji = vehicleType == 'mototaxi' ? '🛺' : '🚗';
    
    // Crear bitmap descriptor con el emoji
    final icon = await _createBitmapDescriptor(emoji, isOnline);

    return Marker(
      markerId: MarkerId(driverId),
      position: position,
      icon: icon,
      anchor: const Offset(0.5, 0.5),
      zIndex: 1.0,
    );
  }

  /// Crea un BitmapDescriptor con el emoji del vehículo.
  static Future<BitmapDescriptor> _createBitmapDescriptor(
    String emoji,
    bool isOnline,
  ) async {
    // Usar default marker ya que crear bitmaps personalizados
    // requiere información adicional del contexto
    return BitmapDescriptor.defaultMarkerWithHue(
      isOnline ? BitmapDescriptor.hueOrange : BitmapDescriptor.hueViolet,
    );
  }
}

/// Marcador de origen (punto de recogida).
Marker createOriginMarker(LatLng position) {
  return Marker(
    markerId: const MarkerId('origin'),
    position: position,
    icon: BitmapDescriptor.defaultMarkerWithHue(BitmapDescriptor.hueGreen),
    zIndex: 2.0,
    infoWindow: const InfoWindow(title: 'Origen'),
  );
}

/// Marcador de destino.
Marker createDestinationMarker(LatLng position) {
  return Marker(
    markerId: const MarkerId('destination'),
    position: position,
    icon: BitmapDescriptor.defaultMarkerWithHue(BitmapDescriptor.hueOrange),
    zIndex: 2.0,
    infoWindow: const InfoWindow(title: 'Destino'),
  );
}