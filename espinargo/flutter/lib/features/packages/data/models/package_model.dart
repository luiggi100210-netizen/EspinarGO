import '../../../../core/utils/formatters.dart';
import '../../../auth/data/models/user_model.dart';

/// Modelo completo de una encomienda.
class PackageModel {
  final String id;
  final String trackingCode;
  final UserModel? sender;
  final UserModel? driver;
  final String recipientName;
  final String recipientPhone;
  final String deliveryAddress;
  final String? deliveryLat;
  final String? deliveryLng;
  final String size;
  final String description;
  final bool isFragile;
  final String? photoUrl;
  final String status;
  final String? price;
  final String paymentMethod;
  final String createdAt;
  final String? pickedUpAt;
  final String? deliveredAt;

  const PackageModel({
    required this.id,
    required this.trackingCode,
    this.sender,
    this.driver,
    required this.recipientName,
    required this.recipientPhone,
    required this.deliveryAddress,
    this.deliveryLat,
    this.deliveryLng,
    required this.size,
    required this.description,
    this.isFragile = false,
    this.photoUrl,
    required this.status,
    this.price,
    required this.paymentMethod,
    required this.createdAt,
    this.pickedUpAt,
    this.deliveredAt,
  });

  factory PackageModel.fromJson(Map<String, dynamic> json) {
    return PackageModel(
      id: json['id'] as String,
      trackingCode: json['tracking_code'] as String,
      sender: json['sender'] != null
          ? UserModel.fromJson(json['sender'] as Map<String, dynamic>)
          : null,
      driver: json['driver'] != null
          ? UserModel.fromJson(json['driver'] as Map<String, dynamic>)
          : null,
      recipientName: json['recipient_name'] as String,
      recipientPhone: json['recipient_phone'] as String,
      deliveryAddress: json['delivery_address'] as String,
      deliveryLat: json['delivery_lat'] as String?,
      deliveryLng: json['delivery_lng'] as String?,
      size: json['size'] as String? ?? 'medium',
      description: json['description'] as String? ?? '',
      isFragile: json['is_fragile'] as bool? ?? false,
      photoUrl: json['photo_url'] as String?,
      status: json['status'] as String? ?? 'pending',
      price: json['price'] as String?,
      paymentMethod: json['payment_method'] as String? ?? 'cash',
      createdAt: json['created_at'] as String? ?? '',
      pickedUpAt: json['picked_up_at'] as String?,
      deliveredAt: json['delivered_at'] as String?,
    );
  }

  Map<String, dynamic> toJson() {
    return {
      'id': id,
      'tracking_code': trackingCode,
      'sender': sender?.toJson(),
      'driver': driver?.toJson(),
      'recipient_name': recipientName,
      'recipient_phone': recipientPhone,
      'delivery_address': deliveryAddress,
      'delivery_lat': deliveryLat,
      'delivery_lng': deliveryLng,
      'size': size,
      'description': description,
      'is_fragile': isFragile,
      'photo_url': photoUrl,
      'status': status,
      'price': price,
      'payment_method': paymentMethod,
      'created_at': createdAt,
      'picked_up_at': pickedUpAt,
      'delivered_at': deliveredAt,
    };
  }

  PackageModel copyWith({
    String? id,
    String? trackingCode,
    UserModel? sender,
    UserModel? driver,
    String? recipientName,
    String? recipientPhone,
    String? deliveryAddress,
    String? deliveryLat,
    String? deliveryLng,
    String? size,
    String? description,
    bool? isFragile,
    String? photoUrl,
    String? status,
    String? price,
    String? paymentMethod,
    String? createdAt,
    String? pickedUpAt,
    String? deliveredAt,
  }) {
    return PackageModel(
      id: id ?? this.id,
      trackingCode: trackingCode ?? this.trackingCode,
      sender: sender ?? this.sender,
      driver: driver ?? this.driver,
      recipientName: recipientName ?? this.recipientName,
      recipientPhone: recipientPhone ?? this.recipientPhone,
      deliveryAddress: deliveryAddress ?? this.deliveryAddress,
      deliveryLat: deliveryLat ?? this.deliveryLat,
      deliveryLng: deliveryLng ?? this.deliveryLng,
      size: size ?? this.size,
      description: description ?? this.description,
      isFragile: isFragile ?? this.isFragile,
      photoUrl: photoUrl ?? this.photoUrl,
      status: status ?? this.status,
      price: price ?? this.price,
      paymentMethod: paymentMethod ?? this.paymentMethod,
      createdAt: createdAt ?? this.createdAt,
      pickedUpAt: pickedUpAt ?? this.pickedUpAt,
      deliveredAt: deliveredAt ?? this.deliveredAt,
    );
  }

  bool get isActive => ['pending', 'assigned', 'picked_up', 'in_transit'].contains(status);
  bool get isDelivered => status == 'delivered';
  bool get isCancelled => status == 'cancelled';

  String get statusLabel => Formatters.packageStatus(status);

  String get sizeLabel {
    switch (size) {
      case 'envelope':
        return 'Sobre / Documento';
      case 'small':
        return 'Paquete pequeño';
      case 'medium':
        return 'Paquete mediano';
      case 'large':
        return 'Paquete grande';
      default:
        return 'Paquete';
    }
  }

  String get sizeEmoji {
    switch (size) {
      case 'envelope':
        return '✉️';
      case 'small':
        return '📦';
      case 'medium':
        return '🗃️';
      case 'large':
        return '📫';
      default:
        return '📦';
    }
  }

  String get formattedPrice {
    if (price != null) return Formatters.currencyFromString(price!);
    return 'Por calcular';
  }

  String get shortTrackingCode => trackingCode;
}