import 'package:flutter/material.dart';

import '../../../../core/theme/app_colors.dart';
import '../../../../core/theme/app_text_styles.dart';
import '../../../auth/data/models/user_model.dart';
import '../../../trips/data/models/trip_model.dart';

/// Card con información del pasajero.
class PassengerInfoCard extends StatelessWidget {
  final UserModel passenger;
  final TripModel trip;
  final VoidCallback onCallPassenger;
  final VoidCallback onWhatsAppPassenger;

  const PassengerInfoCard({
    super.key,
    required this.passenger,
    required this.trip,
    required this.onCallPassenger,
    required this.onWhatsAppPassenger,
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
          ),
        ],
      ),
      child: Column(
        children: [
          // Info del pasajero
          Row(
            children: [
              CircleAvatar(
                radius: 24,
                backgroundColor: AppColors.primary,
                child: Text(
                  passenger.initials,
                  style: AppTextStyles.labelLarge.copyWith(color: Colors.white),
                ),
              ),
              const SizedBox(width: 12),
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(passenger.fullName, style: AppTextStyles.labelLarge),
                    Row(
                      children: [
                        const Icon(Icons.star, color: AppColors.warning, size: 16),
                        const SizedBox(width: 4),
                        Text(
                          '4.6 · 23 viajes',
                          style: AppTextStyles.bodySmall,
                        ),
                      ],
                    ),
                  ],
                ),
              ),
            ],
          ),
          const SizedBox(height: 16),

          // Direcciones
          Row(
            children: [
              Column(
                children: [
                  Container(
                    width: 10,
                    height: 10,
                    decoration: const BoxDecoration(
                      color: AppColors.success,
                      shape: BoxShape.circle,
                    ),
                  ),
                  Container(
                    width: 2,
                    height: 30,
                    color: AppColors.border,
                  ),
                  Container(
                    width: 10,
                    height: 10,
                    decoration: const BoxDecoration(
                      color: AppColors.primary,
                      shape: BoxShape.circle,
                    ),
                  ),
                ],
              ),
              const SizedBox(width: 12),
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(trip.originAddress, style: AppTextStyles.bodyMedium, maxLines: 1),
                    const SizedBox(height: 24),
                    Text(trip.destAddress, style: AppTextStyles.bodyMedium, maxLines: 1),
                  ],
                ),
              ),
            ],
          ),
          const SizedBox(height: 16),

          // Precio
          Row(
            mainAxisAlignment: MainAxisAlignment.spaceBetween,
            children: [
              Text(trip.displayPrice, style: AppTextStyles.priceMedium),
              Text(trip.paymentMethod, style: AppTextStyles.bodySmall),
            ],
          ),
          const SizedBox(height: 16),

          // Botones de contacto
          Row(
            children: [
              Expanded(
                child: OutlinedButton.icon(
                  onPressed: onCallPassenger,
                  icon: const Icon(Icons.phone, color: AppColors.success),
                  label: const Text('Llamar'),
                  style: OutlinedButton.styleFrom(
                    foregroundColor: AppColors.success,
                  ),
                ),
              ),
              const SizedBox(width: 12),
              Expanded(
                child: OutlinedButton.icon(
                  onPressed: onWhatsAppPassenger,
                  icon: const Icon(Icons.chat, color: AppColors.success),
                  label: const Text('WhatsApp'),
                  style: OutlinedButton.styleFrom(
                    foregroundColor: AppColors.success,
                  ),
                ),
              ),
            ],
          ),
        ],
      ),
    );
  }
}