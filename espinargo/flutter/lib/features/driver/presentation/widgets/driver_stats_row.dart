import 'package:flutter/material.dart';

import '../../../../core/theme/app_colors.dart';
import '../../../../core/theme/app_text_styles.dart';

/// Fila de estadísticas del conductor.
class DriverStatsRow extends StatelessWidget {
  final int totalTrips;
  final double rating;
  final double? acceptanceRate;

  const DriverStatsRow({
    super.key,
    required this.totalTrips,
    required this.rating,
    this.acceptanceRate,
  });

  @override
  Widget build(BuildContext context) {
    return Container(
      height: 60,
      decoration: BoxDecoration(
        color: Colors.white,
        borderRadius: BorderRadius.circular(12),
        border: Border.all(color: AppColors.border),
      ),
      child: Row(
        children: [
          _buildStatItem(
            label: 'Viajes',
            value: totalTrips.toString(),
          ),
          _buildDivider(),
          _buildStatItem(
            label: 'Calificación',
            value: rating.toStringAsFixed(1),
            suffix: ' ★',
          ),
          _buildDivider(),
          _buildStatItem(
            label: 'Aceptación',
            value: acceptanceRate != null
                ? '${acceptanceRate!.toStringAsFixed(0)}%'
                : 'N/A',
          ),
        ],
      ),
    );
  }

  Widget _buildStatItem({
    required String label,
    required String value,
    String suffix = '',
  }) {
    return Expanded(
      child: Column(
        mainAxisAlignment: MainAxisAlignment.center,
        children: [
          Text(
            label,
            style: AppTextStyles.labelSmall.copyWith(
              color: AppColors.textSecondary,
            ),
          ),
          Text(
            '$value$suffix',
            style: AppTextStyles.labelLarge.copyWith(
              fontWeight: FontWeight.bold,
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildDivider() {
    return Container(
      width: 1,
      height: 30,
      color: AppColors.border,
    );
  }
}