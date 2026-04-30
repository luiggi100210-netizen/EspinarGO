import 'package:flutter/material.dart';

import '../../../../core/theme/app_colors.dart';
import '../../../../core/theme/app_text_styles.dart';
import '../../data/models/trip_model.dart';

/// Card informativa con el resumen del viaje.
class TripInfoCard extends StatelessWidget {
  final TripModel trip;
  final bool showDriver;

  const TripInfoCard({
    super.key,
    required this.trip,
    this.showDriver = false,
  });

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        color: Colors.white,
        borderRadius: BorderRadius.circular(16),
        boxShadow: [
          BoxShadow(
            color: Colors.black.withOpacity(0.05),
            blurRadius: 10,
            offset: const Offset(0, 2),
          ),
        ],
      ),
      child: Column(
        children: [
          // Ruta
          Row(
            children: [
              // Línea de ruta
              Column(
                children: [
                  Container(
                    width: 12,
                    height: 12,
                    decoration: const BoxDecoration(
                      color: AppColors.success,
                      shape: BoxShape.circle,
                    ),
                  ),
                  Container(
                    width: 2,
                    height: 40,
                    color: AppColors.border,
                  ),
                  Container(
                    width: 12,
                    height: 12,
                    decoration: const BoxDecoration(
                      color: AppColors.primary,
                      shape: BoxShape.circle,
                    ),
                  ),
                ],
              ),
              const SizedBox(width: 12),
              // Direcciones
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(
                      trip.originAddress,
                      style: AppTextStyles.bodyMedium,
                      maxLines: 1,
                      overflow: TextOverflow.ellipsis,
                    ),
                    const SizedBox(height: 24),
                    Text(
                      trip.destAddress,
                      style: AppTextStyles.bodyMedium,
                      maxLines: 1,
                      overflow: TextOverflow.ellipsis,
                    ),
                  ],
                ),
              ),
              // Precio
              Column(
                crossAxisAlignment: CrossAxisAlignment.end,
                children: [
                  Text(
                    trip.displayPrice,
                    style: AppTextStyles.priceMedium,
                  ),
                  if (trip.distanceKm != null)
                    Text(
                      trip.distanceKm!,
                      style: AppTextStyles.labelSmall,
                    ),
                ],
              ),
            ],
          ),

          // Método de pago
          if (trip.paymentMethod != 'cash')
            Padding(
              padding: const EdgeInsets.only(top: 12),
              child: Row(
                children: [
                  Icon(
                    trip.paymentMethod == 'yape' ? Icons.payment : Icons.phone_android,
                    size: 16,
                    color: AppColors.textSecondary,
                  ),
                  const SizedBox(width: 8),
                  Text(
                    trip.paymentMethod == 'yape' ? 'Yape' : 'Plin',
                    style: AppTextStyles.labelSmall,
                  ),
                ],
              ),
            ),

          // Info del conductor
          if (showDriver && trip.driver != null) ...[
            const Divider(height: 24),
            Row(
              children: [
                CircleAvatar(
                  radius: 20,
                  backgroundColor: AppColors.primary,
                  child: Text(
                    trip.driver!.initials,
                    style: AppTextStyles.labelMedium.copyWith(color: Colors.white),
                  ),
                ),
                const SizedBox(width: 12),
                Expanded(
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text(trip.driver!.fullName, style: AppTextStyles.labelLarge),
                      Text(
                        '⭐ 5.0 · 120 viajes',
                        style: AppTextStyles.bodySmall,
                      ),
                    ],
                  ),
                ),
              ],
            ),
          ],
        ],
      ),
    );
  }
}