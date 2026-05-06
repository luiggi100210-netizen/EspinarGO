import 'package:geolocator/geolocator.dart';
import 'package:google_maps_flutter/google_maps_flutter.dart';

import '../../../../core/constants/app_constants.dart';
import '../../../../core/utils/logger.dart';

/// Servicio para manejar la ubicación del usuario.
/// Pide permisos, obtiene posición actual y escucha cambios.
class LocationService {
  /// Solicita permiso de ubicación y retorna true si se otorga.
  static Future<bool> requestPermission() async {
    LocationPermission permission = await Geolocator.checkPermission();

    if (permission == LocationPermission.denied) {
      permission = await Geolocator.requestPermission();
    }

    if (permission == LocationPermission.deniedForever) {
      await Geolocator.openAppSettings();
      return false;
    }

    return permission == LocationPermission.whileInUse ||
        permission == LocationPermission.always;
  }

  /// Obtiene la posición actual del GPS.
  static Future<Position?> getCurrentPosition() async {
    final hasPermission = await requestPermission();
    if (!hasPermission) {
      return null;
    }

    try {
      return await Geolocator.getCurrentPosition(
        desiredAccuracy: LocationAccuracy.high,
        timeLimit: const Duration(seconds: 10),
      );
    } catch (e) {
      AppLogger.error('Error obtaining position', error: e);
      return null;
    }
  }

  /// Verifica si el GPS está habilitado en el dispositivo.
  static Future<bool> isLocationEnabled() async {
    return await Geolocator.isLocationServiceEnabled();
  }

  /// Stream de actualizaciones de posición.
  static Stream<Position> positionStream() {
    return Geolocator.getPositionStream(
      locationSettings: const LocationSettings(
        accuracy: LocationAccuracy.high,
        distanceFilter: 10, // actualizar cada 10 metros
      ),
    );
  }

  /// Centro de Espinar por defecto.
  static LatLng espinarCenter() {
    return LatLng(
      AppConstants.ESPINAR_LAT,
      AppConstants.ESPINAR_LNG,
    );
  }

  /// Calcula la distancia en kilómetros entre dos puntos.
  static double calculateDistance(LatLng origin, LatLng destination) {
    final distanceMeters = Geolocator.distanceBetween(
      origin.latitude,
      origin.longitude,
      destination.latitude,
      destination.longitude,
    );
    return (distanceMeters / 1000).roundToDouble();
  }
}