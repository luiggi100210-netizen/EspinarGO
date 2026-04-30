import 'package:flutter/material.dart';

import '../../../../core/theme/app_colors.dart';
import '../../../../core/theme/app_text_styles.dart';

/// Barra de estado del viaje que aparece en la parte superior.
class TripStatusBar extends StatelessWidget {
  final String status;
  final String? driverName;
  final String? estimatedArrival;

  const TripStatusBar({
    super.key,
    required this.status,
    this.driverName,
    this.estimatedArrival,
  });

  IconData _getStatusIcon() {
    switch (status) {
      case 'searching':
        return Icons.access_time;
      case 'accepted':
        return Icons.directions_car;
      case 'driverArrived':
        return Icons.location_on;
      case 'inProgress':
        return Icons.flag;
      default:
        return Icons.info;
    }
  }

  @override
  Widget build(BuildContext context) {
    return Container(
      width: double.infinity,
      padding: const EdgeInsets.symmetric(vertical: 12, horizontal: 16),
      decoration: const BoxDecoration(
        color: AppColors.primary,
        borderRadius: BorderRadius.vertical(bottom: Radius.circular(16)),
      ),
      child: SafeArea(
        bottom: false,
        child: Row(
          children: [
            Icon(_getStatusIcon(), color: Colors.white, size: 20),
            const SizedBox(width: 8),
            Expanded(
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                mainAxisSize: MainAxisSize.min,
                children: [
                  Text(
                    status,
                    style: AppTextStyles.labelLarge.copyWith(color: Colors.white),
                  ),
                  if (driverName != null)
                    Text(
                      'Conductor: $driverName',
                      style: AppTextStyles.labelSmall.copyWith(
                        color: Colors.white.withOpacity(0.8),
                      ),
                    ),
                ],
              ),
            ),
            if (estimatedArrival != null)
              Text(
                'Llega en $estimatedArrival',
                style: AppTextStyles.labelSmall.copyWith(
                  color: Colors.white.withOpacity(0.8),
                ),
              ),
          ],
        ),
      ),
    );
  }
}