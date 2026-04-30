import 'package:google_maps_flutter/google_maps_flutter.dart';

import '../../../../core/utils/formatters.dart';

/// Modelo para lugares de Google Places API.
/// Representa un resultado de búsqueda de destino.
class PlaceModel {
  final String placeId;
  final String name;
  final String address;
  final double lat;
  final double lng;
  final double? distanceKm;

  const PlaceModel({
    required this.placeId,
    required this.name,
    required this.address,
    required this.lat,
    required this.lng,
    this.distanceKm,
  });

  /// Crea un PlaceModel desde la respuesta de Google Geocoding API.
  factory PlaceModel.fromJson(Map<String, dynamic> json) {
    final location = json['geometry']?['location'] as Map<String, dynamic>?;

    return PlaceModel(
      placeId: json['place_id'] as String? ?? '',
      name: json['formatted_address']?.toString().split(',').first.trim() ?? '',
      address: json['formatted_address'] as String? ?? '',
      lat: (location?['lat'] as num?)?.toDouble() ?? 0.0,
      lng: (location?['lng'] as num?)?.toDouble() ?? 0.0,
    );
  }

  /// Convierte el modelo a LatLng para Google Maps.
  LatLng toLatLng() => LatLng(lat, lng);

  /// Crea una copia con la distancia actualizada.
  PlaceModel copyWith({double? distanceKm}) {
    return PlaceModel(
      placeId: placeId,
      name: name,
      address: address,
      lat: lat,
      lng: lng,
      distanceKm: distanceKm ?? this.distanceKm,
    );
  }

  /// Retorna la distancia formateada (ej: "1.2 km").
  String get formattedDistance {
    if (distanceKm == null) return '';
    return Formatters.distance(distanceKm!);
  }

  /// Retorna la primera parte de la dirección.
  String get shortAddress {
    final parts = address.split(',');
    return parts.first.trim();
  }

  @override
  String toString() {
    return 'PlaceModel(name: $name, lat: $lat, lng: $lng)';
  }
}