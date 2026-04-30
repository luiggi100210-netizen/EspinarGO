import '../../../../core/utils/formatters.dart';
import '../../../auth/data/models/user_model.dart';

/// Modelo de la oferta de un conductor al viaje del pasajero.
/// El núcleo de la lógica InDrive.
class TripOfferModel {
  final String id;
  final String tripId;
  final UserModel driver;
  final Map<String, dynamic>? driverProfile;
  final String offeredPrice;
  final String? message;
  final bool isAccepted;
  final String expiresAt;
  final String createdAt;

  const TripOfferModel({
    required this.id,
    required this.tripId,
    required this.driver,
    this.driverProfile,
    required this.offeredPrice,
    this.message,
    this.isAccepted = false,
    required this.expiresAt,
    required this.createdAt,
  });

  /// Crea desde JSON.
  factory TripOfferModel.fromJson(Map<String, dynamic> json) {
    return TripOfferModel(
      id: json['id'] as String,
      tripId: json['trip_id'] as String,
      driver: UserModel.fromJson(json['driver'] as Map<String, dynamic>),
      driverProfile: json['driver_profile'] as Map<String, dynamic>?,
      offeredPrice: json['offered_price'] as String,
      message: json['message'] as String?,
      isAccepted: json['is_accepted'] as bool? ?? false,
      expiresAt: json['expires_at'] as String,
      createdAt: json['created_at'] as String,
    );
  }

  /// Convierte a JSON.
  Map<String, dynamic> toJson() {
    return {
      'id': id,
      'trip_id': tripId,
      'driver': driver.toJson(),
      'driver_profile': driverProfile,
      'offered_price': offeredPrice,
      'message': message,
      'is_accepted': isAccepted,
      'expires_at': expiresAt,
      'created_at': createdAt,
    };
  }

  /// Crea copia con campos actualizados.
  TripOfferModel copyWith({
    String? id,
    String? tripId,
    UserModel? driver,
    Map<String, dynamic>? driverProfile,
    String? offeredPrice,
    String? message,
    bool? isAccepted,
    String? expiresAt,
    String? createdAt,
  }) {
    return TripOfferModel(
      id: id ?? this.id,
      tripId: tripId ?? this.tripId,
      driver: driver ?? this.driver,
      driverProfile: driverProfile ?? this.driverProfile,
      offeredPrice: offeredPrice ?? this.offeredPrice,
      message: message ?? this.message,
      isAccepted: isAccepted ?? this.isAccepted,
      expiresAt: expiresAt ?? this.expiresAt,
      createdAt: createdAt ?? this.createdAt,
    );
  }

  /// Verifica si la oferta ya expiró.
  bool get isExpired {
    try {
      return DateTime.parse(expiresAt).isBefore(DateTime.now());
    } catch (_) {
      return false;
    }
  }

  /// Precio formateado.
  String get formattedPrice => Formatters.currencyFromString(offeredPrice);

  /// Tipo de vehículo del conductor.
  String get vehicleType => driverProfile?['vehicle_type'] as String? ?? 'mototaxi';

  /// Placa del vehículo.
  String get vehiclePlate => driverProfile?['vehicle_plate'] as String? ?? 'Sin placa';

  /// Rating del conductor.
  double get driverRating {
    final rating = driverProfile?['rating_display'];
    if (rating is double) return rating;
    if (rating is int) return rating.toDouble();
    return 5.0;
  }

  /// Total de viajes del conductor.
  int get driverTrips => driverProfile?['total_trips'] as int? ?? 0;

  /// Tiempo hasta que expira la oferta en formato mm:ss.
  String get timeUntilExpiry {
    try {
      final expiry = DateTime.parse(expiresAt);
      final now = DateTime.now();
      final diff = expiry.difference(now);

      if (diff.isNegative) return '0:00';

      final minutes = diff.inMinutes;
      final seconds = diff.inSeconds % 60;

      return '$minutes:${seconds.toString().padLeft(2, '0')}';
    } catch (_) {
      return '2:00';
    }
  }

  @override
  String toString() {
    return 'TripOfferModel(id: $id, price: $formattedPrice, expires: $timeUntilExpiry)';
  }
}