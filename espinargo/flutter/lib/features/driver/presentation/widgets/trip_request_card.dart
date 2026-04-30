import 'package:flutter/material.dart';

import '../../../../core/theme/app_colors.dart';
import '../../../../core/theme/app_text_styles.dart';
import '../../../../core/utils/formatters.dart';
import '../../../../features/trips/presentation/widgets/countdown_timer.dart';

/// Card que muestra una solicitud de viaje al conductor.
class TripRequestCard extends StatelessWidget {
  final Map<String, dynamic> request;
  final double? distanceFromDriver;
  final VoidCallback onMakeOffer;
  final VoidCallback onReject;

  const TripRequestCard({
    super.key,
    required this.request,
    this.distanceFromDriver,
    required this.onMakeOffer,
    required this.onReject,
  });

  @override
  Widget build(BuildContext context) {
    final proposedPrice = double.tryParse(request['proposed_price']?.toString() ?? '0') ?? 0;
    final distanceKm = double.tryParse(request['distance_km']?.toString() ?? '0') ?? 0;

    return Container(
      margin: const EdgeInsets.only(bottom: 12),
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        color: Colors.white,
        borderRadius: BorderRadius.circular(16),
        border: Border.all(color: AppColors.primary, width: 2),
        boxShadow: [
          BoxShadow(
            color: AppColors.primary.withOpacity(0.1),
            blurRadius: 10,
            offset: const Offset(0, 4),
          ),
        ],
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          // Badge nueva solicitud
          Container(
            padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
            decoration: BoxDecoration(
              color: AppColors.error.withOpacity(0.1),
              borderRadius: BorderRadius.circular(8),
            ),
            child: Row(
              mainAxisSize: MainAxisSize.min,
              children: [
                Container(
                  width: 8,
                  height: 8,
                  decoration: const BoxDecoration(
                    color: AppColors.error,
                    shape: BoxShape.circle,
                  ),
                ),
                const SizedBox(width: 6),
                Text(
                  'NUEVA SOLICITUD',
                  style: AppTextStyles.labelSmall.copyWith(
                    color: AppColors.error,
                    fontWeight: FontWeight.bold,
                  ),
                ),
              ],
            ),
          ),
          const SizedBox(height: 12),

          // Origen
          Row(
            children: [
              const Icon(Icons.location_on, color: AppColors.success, size: 20),
              const SizedBox(width: 8),
              Expanded(
                child: Text(
                  request['origin_address'] ?? 'Origen',
                  style: AppTextStyles.bodyMedium,
                  maxLines: 1,
                  overflow: TextOverflow.ellipsis,
                ),
              ),
            ],
          ),
          const SizedBox(height: 8),

          // Destino
          Row(
            children: [
              const Icon(Icons.flag, color: AppColors.primary, size: 20),
              const SizedBox(width: 8),
              Expanded(
                child: Text(
                  request['dest_address'] ?? 'Destino',
                  style: AppTextStyles.bodyMedium,
                  maxLines: 1,
                  overflow: TextOverflow.ellipsis,
                ),
              ),
            ],
          ),
          const SizedBox(height: 16),

          // Precio y distancia
          Row(
            mainAxisAlignment: MainAxisAlignment.spaceBetween,
            children: [
              Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text('Precio', style: AppTextStyles.labelSmall),
                  Text(
                    Formatters.currency(proposedPrice),
                    style: AppTextStyles.priceDisplay,
                  ),
                ],
              ),
              Column(
                crossAxisAlignment: CrossAxisAlignment.end,
                children: [
                  Text('Distancia', style: AppTextStyles.labelSmall),
                  Text(
                    Formatters.distance(distanceKm),
                    style: AppTextStyles.labelMedium,
                  ),
                  if (distanceFromDriver != null)
                    Text(
                      'A ${Formatters.distance(distanceFromDriver!)} de ti',
                      style: AppTextStyles.bodySmall.copyWith(
                        color: AppColors.textSecondary,
                      ),
                    ),
                ],
              ),
            ],
          ),
          const SizedBox(height: 16),

          // Countdown
          CountdownTimer(
            expiresAt: DateTime.now().add(const Duration(seconds: 30)),
            onExpired: onReject,
            style: AppTextStyles.labelMedium.copyWith(
              color: AppColors.error,
            ),
          ),
          const SizedBox(height: 12),

          // Botones
          Row(
            children: [
              Expanded(
                child: OutlinedButton(
                  onPressed: onReject,
                  style: OutlinedButton.styleFrom(
                    foregroundColor: AppColors.textSecondary,
                  ),
                  child: const Text('Ignorar'),
                ),
              ),
              const SizedBox(width: 12),
              Expanded(
                child: ElevatedButton(
                  onPressed: onMakeOffer,
                  style: ElevatedButton.styleFrom(
                    backgroundColor: AppColors.success,
                  ),
                  child: const Text('Hacer oferta'),
                ),
              ),
            ],
          ),
        ],
      ),
    );
  }
}