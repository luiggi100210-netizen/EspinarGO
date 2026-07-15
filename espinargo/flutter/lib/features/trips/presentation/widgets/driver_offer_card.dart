import 'package:flutter/material.dart';

import '../../../../core/theme/app_colors.dart';
import '../../../../core/theme/app_text_styles.dart';
import '../../data/models/trip_offer_model.dart';
import 'countdown_timer.dart';

/// Card que muestra la oferta de un conductor.
class DriverOfferCard extends StatelessWidget {
  final TripOfferModel offer;
  final VoidCallback onAccept;
  final bool isSelected;
  final String? proposedPrice;

  const DriverOfferCard({
    super.key,
    required this.offer,
    required this.onAccept,
    this.isSelected = false,
    this.proposedPrice,
  });

  @override
  Widget build(BuildContext context) {
    final proposed = double.tryParse(proposedPrice ?? '0') ?? 0;
    final offered = double.tryParse(offer.offeredPrice) ?? 0;

    String priceBadge;
    Color badgeColor;
    if (offered < proposed) {
      priceBadge = 'Más barato';
      badgeColor = AppColors.success;
    } else if (offered == proposed) {
      priceBadge = 'Precio propuesto';
      badgeColor = AppColors.info;
    } else {
      priceBadge = 'Mayor al propuesto';
      badgeColor = AppColors.warning;
    }

    return AnimatedContainer(
      duration: const Duration(milliseconds: 200),
      margin: const EdgeInsets.only(bottom: 12),
      decoration: BoxDecoration(
        color: isSelected ? AppColors.primaryLight : Colors.white,
        borderRadius: BorderRadius.circular(16),
        border: Border.all(
          color: isSelected ? AppColors.primary : AppColors.border,
          width: isSelected ? 2 : 1,
        ),
      ),
      child: Column(
        children: [
          // Info del conductor
          Padding(
            padding: const EdgeInsets.all(16),
            child: Row(
              children: [
                // Avatar
                CircleAvatar(
                  radius: 24,
                  backgroundColor: AppColors.primary,
                  child: Text(
                    offer.driver.initials,
                    style: AppTextStyles.labelLarge.copyWith(color: Colors.white),
                  ),
                ),
                const SizedBox(width: 12),
                // Nombre y rating
                Expanded(
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text(offer.driver.fullName, style: AppTextStyles.labelLarge),
                      Row(
                        children: [
                          const Icon(Icons.star, color: AppColors.warning, size: 16),
                          const SizedBox(width: 4),
                          Text(
                            '${offer.driverRating.toStringAsFixed(1)} · ${offer.driverTrips} viajes',
                            style: AppTextStyles.bodySmall,
                          ),
                        ],
                      ),
                    ],
                  ),
                ),
                // Tipo de vehículo
                Container(
                  padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
                  decoration: BoxDecoration(
                    color: AppColors.background,
                    borderRadius: BorderRadius.circular(8),
                  ),
                  child: Text(
                    '${offer.vehicleType == 'mototaxi' ? '🛺' : '🚗'} ${offer.vehiclePlate}',
                    style: AppTextStyles.labelSmall,
                  ),
                ),
              ],
            ),
          ),

          // Precio
          Container(
            padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 12),
            color: isSelected ? AppColors.primary.withOpacity(0.1) : AppColors.background,
            child: Row(
              mainAxisAlignment: MainAxisAlignment.spaceBetween,
              children: [
                Text(
                  offer.formattedPrice,
                  style: AppTextStyles.priceDisplay,
                ),
                Container(
                  padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
                  decoration: BoxDecoration(
                    color: badgeColor.withOpacity(0.1),
                    borderRadius: BorderRadius.circular(8),
                  ),
                  child: Text(
                    priceBadge,
                    style: AppTextStyles.labelSmall.copyWith(color: badgeColor),
                  ),
                ),
              ],
            ),
          ),

          // Mensaje del conductor
          if (offer.message != null)
            Container(
              width: double.infinity,
              padding: const EdgeInsets.all(12),
              child: Text(
                '"${offer.message}"',
                style: AppTextStyles.bodySmall.copyWith(
                  fontStyle: FontStyle.italic,
                ),
              ),
            ),

          // Countdown y botón
          Padding(
            padding: const EdgeInsets.all(16),
            child: Row(
              children: [
                if (!offer.isExpired)
                  CountdownTimer(
                    expiresAt: DateTime.parse(offer.expiresAt),
                    onExpired: () {},
                  ),
                const Spacer(),
                SizedBox(
                  width: 140,
                  child: ElevatedButton(
                    onPressed: onAccept,
                    style: ElevatedButton.styleFrom(
                      backgroundColor: AppColors.primary,
                      padding: const EdgeInsets.symmetric(vertical: 10),
                    ),
                    child: const Text('Aceptar'),
                  ),
                ),
              ],
            ),
          ),
        ],
      ),
    );
  }
}