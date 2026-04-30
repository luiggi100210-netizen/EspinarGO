import 'package:flutter/material.dart';

import '../../../../core/theme/app_colors.dart';
import '../../../../core/utils/formatters.dart';

/// Modelo de un evento en el historial de tracking.
class TrackingEventModel {
  final String id;
  final String status;
  final String description;
  final String createdAt;
  final String? locationLat;
  final String? locationLng;
  final String? updatedBy;

  const TrackingEventModel({
    required this.id,
    required this.status,
    required this.description,
    required this.createdAt,
    this.locationLat,
    this.locationLng,
    this.updatedBy,
  });

  factory TrackingEventModel.fromJson(Map<String, dynamic> json) {
    return TrackingEventModel(
      id: json['id'] as String,
      status: json['status'] as String,
      description: json['description'] as String? ?? '',
      createdAt: json['created_at'] as String,
      locationLat: json['location_lat'] as String?,
      locationLng: json['location_lng'] as String?,
      updatedBy: json['updated_by'] as String?,
    );
  }

  String get statusLabel => Formatters.packageStatus(status);
  String get formattedTime => Formatters.dateTime(DateTime.parse(createdAt));
  String get timeAgo => Formatters.timeAgo(DateTime.parse(createdAt));

  Color get statusColor {
    switch (status) {
      case 'delivered':
        return AppColors.success;
      case 'in_transit':
      case 'picked_up':
        return AppColors.info;
      case 'assigned':
        return AppColors.warning;
      case 'pending':
        return AppColors.textSecondary;
      case 'cancelled':
        return AppColors.error;
      default:
        return AppColors.textSecondary;
    }
  }
}