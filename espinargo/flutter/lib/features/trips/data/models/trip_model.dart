import 'package:google_maps_flutter/google_maps_flutter.dart';

import '../../../../core/utils/formatters.dart';
import '../../../auth/data/models/user_model.dart';

/// Modelo completo de un viaje.
/// Representa exactamente lo que retorna la API del backend.
class TripModel {
  final String id;
  final UserModel? passenger;
  final UserModel? driver;
  final String originAddress;
  final String originLat;
  final String originLng;
  final String destAddress;
  final String destLat;
  final String destLng;
  final String proposedPrice;
  final String? finalPrice;
  final String status;
  final String paymentMethod;
  final String? distanceKm;
  final int? durationMinutes;
  final String? cancelReason;
  final String createdAt;
  final String? acceptedAt;
  final String? startedAt;
  final String? completedAt;
  final String? cancelledAt;

  const TripModel({
    required this.id,
    this.passenger,
    this.driver,
    required this.originAddress,
    required this.originLat,
    required this.originLng,
    required this.destAddress,
    required this.destLat,
    required this.destLng,
    required this.proposedPrice,
    this.finalPrice,
    required this.status,
    required this.paymentMethod,
    this.distanceKm,
    this.durationMinutes,
    this.cancelReason,
    required this.createdAt,
    this.acceptedAt,
    this.startedAt,
    this.completedAt,
    this.cancelledAt,
  });

  /// Crea un TripModel desde JSON.
  factory TripModel.fromJson(Map<String, dynamic> json) {
    return TripModel(
      id: json['id'] as String,
      passenger: json['passenger'] != null
          ? (json['passenger'] is Map
              ? UserModel.fromJson(json['passenger'] as Map<String, dynamic>)
              : null)
          : null,
      driver: json['driver'] != null
          ? (json['driver'] is Map
              ? UserModel.fromJson(json['driver'] as Map<String, dynamic>)
              : null)
          : null,
      originAddress: json['origin_address'] as String? ?? '',
      originLat: json['origin_lat'] as String? ?? '0',
      originLng: json['origin_lng'] as String? ?? '0',
      destAddress: json['dest_address'] as String? ?? '',
      destLat: json['dest_lat'] as String? ?? '0',
      destLng: json['dest_lng'] as String? ?? '0',
      proposedPrice: json['proposed_price'] as String? ?? '0',
      finalPrice: json['final_price'] as String?,
      status: json['status'] as String? ?? 'searching',
      paymentMethod: json['payment_method'] as String? ?? 'cash',
      distanceKm: json['distance_km'] as String?,
      durationMinutes: json['duration_minutes'] as int?,
      cancelReason: json['cancel_reason'] as String?,
      createdAt: json['created_at'] as String? ?? '',
      acceptedAt: json['accepted_at'] as String?,
      startedAt: json['started_at'] as String?,
      completedAt: json['completed_at'] as String?,
      cancelledAt: json['cancelled_at'] as String?,
    );
  }

  /// Convierte a JSON.
  Map<String, dynamic> toJson() {
    return {
      'id': id,
      'passenger': passenger?.toJson(),
      'driver': driver?.toJson(),
      'origin_address': originAddress,
      'origin_lat': originLat,
      'origin_lng': originLng,
      'dest_address': destAddress,
      'dest_lat': destLat,
      'dest_lng': destLng,
      'proposed_price': proposedPrice,
      'final_price': finalPrice,
      'status': status,
      'payment_method': paymentMethod,
      'distance_km': distanceKm,
      'duration_minutes': durationMinutes,
      'cancel_reason': cancelReason,
      'created_at': createdAt,
      'accepted_at': acceptedAt,
      'started_at': startedAt,
      'completed_at': completedAt,
      'cancelled_at': cancelledAt,
    };
  }

  /// Crea una copia con campos actualizados.
  TripModel copyWith({
    String? id,
    UserModel? passenger,
    UserModel? driver,
    String? originAddress,
    String? originLat,
    String? originLng,
    String? destAddress,
    String? destLat,
    String? destLng,
    String? proposedPrice,
    String? finalPrice,
    String? status,
    String? paymentMethod,
    String? distanceKm,
    int? durationMinutes,
    String? cancelReason,
    String? createdAt,
    String? acceptedAt,
    String? startedAt,
    String? completedAt,
    String? cancelledAt,
  }) {
    return TripModel(
      id: id ?? this.id,
      passenger: passenger ?? this.passenger,
      driver: driver ?? this.driver,
      originAddress: originAddress ?? this.originAddress,
      originLat: originLat ?? this.originLat,
      originLng: originLng ?? this.originLng,
      destAddress: destAddress ?? this.destAddress,
      destLat: destLat ?? this.destLat,
      destLng: destLng ?? this.destLng,
      proposedPrice: proposedPrice ?? this.proposedPrice,
      finalPrice: finalPrice ?? this.finalPrice,
      status: status ?? this.status,
      paymentMethod: paymentMethod ?? this.paymentMethod,
      distanceKm: distanceKm ?? this.distanceKm,
      durationMinutes: durationMinutes ?? this.durationMinutes,
      cancelReason: cancelReason ?? this.cancelReason,
      createdAt: createdAt ?? this.createdAt,
      acceptedAt: acceptedAt ?? this.acceptedAt,
      startedAt: startedAt ?? this.startedAt,
      completedAt: completedAt ?? this.completedAt,
      cancelledAt: cancelledAt ?? this.cancelledAt,
    );
  }

  /// Verifica si el viaje está activo.
  bool get isActive => ['searching', 'negotiating', 'accepted', 'in_progress'].contains(status);

  /// Verifica si el viaje está completado.
  bool get isCompleted => status == 'completed';

  /// Verifica si el viaje está cancelado.
  bool get isCancelled => status == 'cancelled';

  /// Verifica si hay conductor asignado.
  bool get hasDriver => driver != null;

  /// Retorna las coordenadas del origen.
  LatLng get originLatLng => LatLng(
        double.tryParse(originLat) ?? 0,
        double.tryParse(originLng) ?? 0,
      );

  /// Retorna las coordenadas del destino.
  LatLng get destLatLng => LatLng(
        double.tryParse(destLat) ?? 0,
        double.tryParse(destLng) ?? 0,
      );

  /// Texto del estado del viaje.
  String get statusText => Formatters.tripStatus(status);

  /// Precio a mostrar (final si existe, sino propuesto).
  String get displayPrice {
    if (finalPrice != null) {
      return Formatters.currencyFromString(finalPrice!);
    }
    return Formatters.currencyFromString(proposedPrice);
  }

  @override
  String toString() {
    return 'TripModel(id: $id, status: $status, price: $displayPrice)';
  }
}