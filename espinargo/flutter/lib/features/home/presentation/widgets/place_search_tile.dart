import 'package:flutter/material.dart';

import '../../../../core/theme/app_colors.dart';
import '../../../../core/theme/app_text_styles.dart';
import '../../data/models/place_model.dart';

/// Tile para mostrar un resultado de búsqueda de lugar.
class PlaceSearchTile extends StatelessWidget {
  final PlaceModel place;
  final VoidCallback onTap;

  const PlaceSearchTile({
    super.key,
    required this.place,
    required this.onTap,
  });

  @override
  Widget build(BuildContext context) {
    return InkWell(
      onTap: onTap,
      child: Container(
        padding: const EdgeInsets.symmetric(vertical: 12, horizontal: 16),
        child: Row(
          children: [
            // Ícono de pin
            const Icon(
              Icons.location_on,
              color: AppColors.primary,
              size: 24,
            ),
            const SizedBox(width: 12),
            // Nombre y dirección
            Expanded(
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(
                    place.name,
                    style: AppTextStyles.bodyMedium,
                    maxLines: 1,
                    overflow: TextOverflow.ellipsis,
                  ),
                  const SizedBox(height: 2),
                  Text(
                    place.shortAddress,
                    style: AppTextStyles.bodySmall,
                    maxLines: 1,
                    overflow: TextOverflow.ellipsis,
                  ),
                ],
              ),
            ),
            // Distancia
            if (place.distanceKm != null)
              Text(
                place.formattedDistance,
                style: AppTextStyles.labelSmall.copyWith(
                  color: AppColors.textDisabled,
                ),
              ),
          ],
        ),
      ),
    );
  }
}