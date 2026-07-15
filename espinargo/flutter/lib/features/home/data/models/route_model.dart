import 'package:google_maps_flutter/google_maps_flutter.dart';

import '../../../../core/utils/formatters.dart';
import 'place_model.dart';

/// Modelo para la ruta calculada entre origen y destino.
class RouteModel {
  final PlaceModel origin;
  final PlaceModel destination;
  final double distanceKm;
  final int durationMinutes;
  final List<LatLng> polylinePoints;
  final double suggestedPrice;
  final double minPrice;
  final double maxPrice;

  const RouteModel({
    required this.origin,
    required this.destination,
    required this.distanceKm,
    required this.durationMinutes,
    required this.polylinePoints,
    required this.suggestedPrice,
    required this.minPrice,
    required this.maxPrice,
  });

  /// Crea un RouteModel desde la respuesta de Google Directions API.
  factory RouteModel.fromDirectionsResponse(
    Map<String, dynamic> json,
    PlaceModel origin,
    PlaceModel destination,
  ) {
    final routes = json['routes'] as List<dynamic>?;
    if (routes == null || routes.isEmpty) {
      throw Exception('No se encontró una ruta');
    }

    final route = routes.first as Map<String, dynamic>;
    final legs = route['legs'] as List<dynamic>?;
    if (legs == null || legs.isEmpty) {
      throw Exception('No hay información de la ruta');
    }

    final leg = legs.first as Map<String, dynamic>;

    // Extraer distancia y tiempo
    final distanceValue = leg['distance']?['value'] as num? ?? 0; // en metros
    final durationValue = leg['duration']?['value'] as num? ?? 0; // en segundos

    // Decodificar polyline
    final encodedPolyline = route['overview_polyline']?['points'] as String? ?? '';
    final points = decodePolyline(encodedPolyline);

    // Calcular precios
    final distanceKm = distanceValue / 1000.0;
    final prices = _calculatePrice(distanceKm);

    return RouteModel(
      origin: origin,
      destination: destination,
      distanceKm: distanceKm,
      durationMinutes: (durationValue / 60).round(),
      polylinePoints: points,
      suggestedPrice: prices['suggested']!,
      minPrice: prices['min']!,
      maxPrice: prices['max']!,
    );
  }

  /// Decodifica el polyline encoded de Google Maps.
  static List<LatLng> decodePolyline(String encoded) {
    final List<LatLng> points = [];
    int index = 0;
    int lat = 0;
    int lng = 0;

    while (index < encoded.length) {
      int shift = 0;
      int result = 0;
      int byte;

      do {
        byte = encoded.codeUnitAt(index++) - 63;
        result |= (byte & 0x1f) << shift;
        shift += 5;
      } while (byte >= 0x20);

      int dlat = (result & 1) != 0 ? ~(result >> 1) : result >> 1;
      lat += dlat;

      shift = 0;
      result = 0;

      do {
        byte = encoded.codeUnitAt(index++) - 63;
        result |= (byte & 0x1f) << shift;
        shift += 5;
      } while (byte >= 0x20);

      int dlng = (result & 1) != 0 ? ~(result >> 1) : result >> 1;
      lng += dlng;

      points.add(LatLng(lat / 1E5, lng / 1E5));
    }

    return points;
  }

  /// Calcula el precio sugerido, mínimo y máximo.
  static Map<String, double> _calculatePrice(double distanceKm) {
    const double pricePerKm = 2.50;
    double suggested;

    if (distanceKm < 1.0) {
      suggested = 3.00;
    } else if (distanceKm <= 3.0) {
      suggested = pricePerKm * distanceKm;
    } else {
      suggested = pricePerKm * distanceKm * 0.9; // descuento por distancia
    }

    // Redondear al 0.50 más cercano
    suggested = (suggested * 2).round() / 2;

    return {
      'suggested': suggested,
      'min': suggested * 0.7,
      'max': suggested * 1.5,
    };
  }

  /// Distancia formateada.
  String get formattedDistance => Formatters.distance(distanceKm);

  /// Duración formateada.
  String get formattedDuration => Formatters.duration(durationMinutes);

  /// Precio sugerido formateado.
  String get suggestedPriceFormatted => Formatters.currency(suggestedPrice);
}