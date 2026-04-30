import 'package:flutter/material.dart';

import '../../../../core/theme/app_colors.dart';
import '../../../../core/theme/app_text_styles.dart';
import '../../../../core/utils/formatters.dart';

/// Card de resumen de ganancias del día.
class EarningsSummaryCard extends StatelessWidget {
  final double todayEarnings;
  final int todayTrips;
  final double? weekEarnings;
  final bool isLoading;
  final VoidCallback? onTap;

  const EarningsSummaryCard({
    super.key,
    required this.todayEarnings,
    required this.todayTrips,
    this.weekEarnings,
    this.isLoading = false,
    this.onTap,
  });

  @override
  Widget build(BuildContext context) {
    return GestureDetector(
      onTap: onTap,
      child: Container(
        padding: const EdgeInsets.all(16),
        decoration: BoxDecoration(
          gradient: LinearGradient(
            colors: [
              AppColors.primaryLight,
              AppColors.primaryLight.withOpacity(0.8),
            ],
            begin: Alignment.topLeft,
            end: Alignment.bottomRight,
          ),
          borderRadius: BorderRadius.circular(16),
        ),
        child: isLoading
            ? const Center(child: CircularProgressIndicator())
            : Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(
                    'Ganancias de hoy',
                    style: AppTextStyles.labelMedium.copyWith(
                      color: AppColors.textSecondary,
                    ),
                  ),
                  const SizedBox(height: 8),
                  Text(
                    Formatters.currency(todayEarnings),
                    style: AppTextStyles.priceDisplay,
                  ),
                  Text(
                    '$todayTrips viajes completados',
                    style: AppTextStyles.bodySmall,
                  ),
                  if (weekEarnings != null) ...[
                    const Divider(height: 24),
                    Row(
                      mainAxisAlignment: MainAxisAlignment.spaceBetween,
                      children: [
                        Text('Esta semana', style: AppTextStyles.labelSmall),
                        Text(
                          Formatters.currency(weekEarnings!),
                          style: AppTextStyles.labelMedium,
                        ),
                      ],
                    ),
                  ],
                ],
              ),
      ),
    );
  }
}