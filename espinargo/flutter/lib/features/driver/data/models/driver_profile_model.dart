import '../../../../core/utils/formatters.dart';

/// Modelo del perfil extendido del conductor.
/// Contiene datos del vehículo, documentos y estadísticas.
class DriverProfileModel {
  final String id;
  final String userId;
  final String? vehicleType;
  final String? vehicleBrand;
  final String? vehicleModel;
  final int? vehicleYear;
  final String? vehicleColor;
  final String? vehiclePlate;
  final int? vehicleSeats;
  final String? vehiclePhotoUrl;
  final String? dniFrontUrl;
  final String? dniBackUrl;
  final String? licenseUrl;
  final String? soatUrl;
  final String? selfieUrl;
  final String driverStatus;
  final String? rejectionReason;
  final int totalTrips;
  final int rating;
  final int ratingCount;
  final bool isOnline;

  const DriverProfileModel({
    required this.id,
    required this.userId,
    this.vehicleType,
    this.vehicleBrand,
    this.vehicleModel,
    this.vehicleYear,
    this.vehicleColor,
    this.vehiclePlate,
    this.vehicleSeats,
    this.vehiclePhotoUrl,
    this.dniFrontUrl,
    this.dniBackUrl,
    this.licenseUrl,
    this.soatUrl,
    this.selfieUrl,
    required this.driverStatus,
    this.rejectionReason,
    this.totalTrips = 0,
    this.rating = 0,
    this.ratingCount = 0,
    this.isOnline = false,
  });

  /// Crea desde JSON.
  factory DriverProfileModel.fromJson(Map<String, dynamic> json) {
    return DriverProfileModel(
      id: json['id'] as String,
      userId: json['user_id'] as String,
      vehicleType: json['vehicle_type'] as String?,
      vehicleBrand: json['vehicle_brand'] as String?,
      vehicleModel: json['vehicle_model'] as String?,
      vehicleYear: json['vehicle_year'] as int?,
      vehicleColor: json['vehicle_color'] as String?,
      vehiclePlate: json['vehicle_plate'] as String?,
      vehicleSeats: json['vehicle_seats'] as int?,
      vehiclePhotoUrl: json['vehicle_photo_url'] as String?,
      dniFrontUrl: json['dni_front_url'] as String?,
      dniBackUrl: json['dni_back_url'] as String?,
      licenseUrl: json['license_url'] as String?,
      soatUrl: json['soat_url'] as String?,
      selfieUrl: json['selfie_url'] as String?,
      driverStatus: json['driver_status'] as String? ?? 'pending_docs',
      rejectionReason: json['rejection_reason'] as String?,
      totalTrips: json['total_trips'] as int? ?? 0,
      rating: json['rating'] as int? ?? 0,
      ratingCount: json['rating_count'] as int? ?? 0,
      isOnline: json['is_online'] as bool? ?? false,
    );
  }

  /// Convierte a JSON.
  Map<String, dynamic> toJson() {
    return {
      'id': id,
      'user_id': userId,
      'vehicle_type': vehicleType,
      'vehicle_brand': vehicleBrand,
      'vehicle_model': vehicleModel,
      'vehicle_year': vehicleYear,
      'vehicle_color': vehicleColor,
      'vehicle_plate': vehiclePlate,
      'vehicle_seats': vehicleSeats,
      'vehicle_photo_url': vehiclePhotoUrl,
      'dni_front_url': dniFrontUrl,
      'dni_back_url': dniBackUrl,
      'license_url': licenseUrl,
      'soat_url': soatUrl,
      'selfie_url': selfieUrl,
      'driver_status': driverStatus,
      'rejection_reason': rejectionReason,
      'total_trips': totalTrips,
      'rating': rating,
      'rating_count': ratingCount,
      'is_online': isOnline,
    };
  }

  /// Crea copia con campos actualizados.
  DriverProfileModel copyWith({
    String? id,
    String? userId,
    String? vehicleType,
    String? vehicleBrand,
    String? vehicleModel,
    int? vehicleYear,
    String? vehicleColor,
    String? vehiclePlate,
    int? vehicleSeats,
    String? vehiclePhotoUrl,
    String? dniFrontUrl,
    String? dniBackUrl,
    String? licenseUrl,
    String? soatUrl,
    String? selfieUrl,
    String? driverStatus,
    String? rejectionReason,
    int? totalTrips,
    int? rating,
    int? ratingCount,
    bool? isOnline,
  }) {
    return DriverProfileModel(
      id: id ?? this.id,
      userId: userId ?? this.userId,
      vehicleType: vehicleType ?? this.vehicleType,
      vehicleBrand: vehicleBrand ?? this.vehicleBrand,
      vehicleModel: vehicleModel ?? this.vehicleModel,
      vehicleYear: vehicleYear ?? this.vehicleYear,
      vehicleColor: vehicleColor ?? this.vehicleColor,
      vehiclePlate: vehiclePlate ?? this.vehiclePlate,
      vehicleSeats: vehicleSeats ?? this.vehicleSeats,
      vehiclePhotoUrl: vehiclePhotoUrl ?? this.vehiclePhotoUrl,
      dniFrontUrl: dniFrontUrl ?? this.dniFrontUrl,
      dniBackUrl: dniBackUrl ?? this.dniBackUrl,
      licenseUrl: licenseUrl ?? this.licenseUrl,
      soatUrl: soatUrl ?? this.soatUrl,
      selfieUrl: selfieUrl ?? this.selfieUrl,
      driverStatus: driverStatus ?? this.driverStatus,
      rejectionReason: rejectionReason ?? this.rejectionReason,
      totalTrips: totalTrips ?? this.totalTrips,
      rating: rating ?? this.rating,
      ratingCount: ratingCount ?? this.ratingCount,
      isOnline: isOnline ?? this.isOnline,
    );
  }

  /// Rating display (0-50 interno → 0.0-5.0 mostrar)
  double get ratingDisplay => rating / 10.0;

  /// Conductor aprobado puede trabajar
  bool get isApproved => driverStatus == 'approved';

  /// Pendiente de subir documentos
  bool get isPendingDocs => driverStatus == 'pending_docs';

  /// En revisión de documentos
  bool get isUnderReview => driverStatus == 'under_review';

  /// Rechazado
  bool get isRejected => driverStatus == 'rejected';

  /// Descripción del vehículo
  String get vehicleDescription {
    if (vehicleBrand != null && vehicleModel != null) {
      return '$vehicleBrand $vehicleModel';
    }
    if (vehicleBrand != null) return vehicleBrand!;
    if (vehicleModel != null) return vehicleModel!;
    return 'Vehículo sin registrar';
  }

  /// Label del tipo de vehículo
  String get vehicleTypeLabel => Formatters.vehicleType(vehicleType ?? 'mototaxi');

  /// Label del status
  String get statusLabel => Formatters.driverStatus(driverStatus);

  /// Puede trabajar (conductor aprobado)
  bool get canWork => isApproved;
}