import 'package:flutter/material.dart';

import '../../../../core/theme/app_colors.dart';
import '../../../../core/theme/app_text_styles.dart';
import '../../data/models/package_model.dart';

/// Card de resumen de una encomienda.
class PackageCard extends StatelessWidget {
  final PackageModel package;
  final VoidCallback onTap;

  const PackageCard({
    super.key,
    required this.package,
    required this.onTap,
  });

  @override
  Widget build(BuildContext context) {
    Color borderColor;
    if (package.isDelivered) borderColor = AppColors.success;
    else if (package.isCancelled) borderColor = AppColors.textDisabled;
    else borderColor = AppColors.package;

    return GestureDetector(
      onTap: onTap,
      child: Container(
        margin: const EdgeInsets.only(bottom: 12),
        decoration: BoxDecoration(
          color: Colors.white,
          borderRadius: BorderRadius.circular(12),
          border: Border(left: BorderSide(color: borderColor, width: 4)),
        ),
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              mainAxisAlignment: MainAxisAlignment.spaceBetween,
              children: [
                Text(package.shortTrackingCode, style: AppTextStyles.trackingCode),
                _buildStatusBadge(package.status),
              ],
            ),
            const SizedBox(height: 8),
            Row(
              children: [
                Text(package.sizeEmoji, style: const TextStyle(fontSize: 20)),
                const SizedBox(width: 8),
                Expanded(
                  child: Text(
                    '${package.sizeLabel} · ${package.recipientName}',
                    style: AppTextStyles.bodyMedium,
                    maxLines: 1,
                    overflow: TextOverflow.ellipsis,
                  ),
                ),
              ],
            ),
            const SizedBox(height: 4),
            Text(package.deliveryAddress, style: AppTextStyles.bodySmall, maxLines: 1, overflow: TextOverflow.ellipsis),
            const SizedBox(height: 8),
            Row(
              mainAxisAlignment: MainAxisAlignment.spaceBetween,
              children: [
                Text(
                  package.createdAt.substring(0, 10),
                  style: AppTextStyles.labelSmall.copyWith(color: AppColors.textDisabled),
                ),
                Text(package.formattedPrice, style: AppTextStyles.priceSmall),
              ],
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildStatusBadge(String status) {
    Color color;
    String text;
    switch (status) {
      case 'delivered':
        color = AppColors.success;
        text = 'Entregado';
        break;
      case 'in_transit':
        color = AppColors.info;
        text = 'En camino';
        break;
      case 'picked_up':
        color = AppColors.info;
        text = 'Recogido';
        break;
      case 'assigned':
        color = AppColors.warning;
        text = 'Asignado';
        break;
      case 'cancelled':
        color = AppColors.error;
        text = 'Cancelado';
        break;
      default:
        color = AppColors.textSecondary;
        text = 'Pendiente';
    }

    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
      decoration: BoxDecoration(color: color.withOpacity(0.1), borderRadius: BorderRadius.circular(8)),
      child: Text(text, style: AppTextStyles.labelSmall.copyWith(color: color)),
    );
  }
}