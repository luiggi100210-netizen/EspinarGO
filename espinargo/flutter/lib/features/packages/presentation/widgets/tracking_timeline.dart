import 'package:flutter/material.dart';

import '../../../../core/theme/app_colors.dart';
import '../../../../core/theme/app_text_styles.dart';
import '../../data/models/tracking_event_model.dart';

/// Timeline visual del historial de tracking.
class TrackingTimeline extends StatelessWidget {
  final List<TrackingEventModel> events;
  final String currentStatus;

  const TrackingTimeline({
    super.key,
    required this.events,
    required this.currentStatus,
  });

  @override
  Widget build(BuildContext context) {
    return ListView.builder(
      shrinkWrap: true,
      physics: const NeverScrollableScrollPhysics(),
      itemCount: events.length,
      itemBuilder: (context, index) {
        final event = events[index];
        final isLast = index == 0;

        return Row(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            // Punto y línea
            Column(
              children: [
                Container(
                  width: isLast ? 16 : 12,
                  height: isLast ? 16 : 12,
                  decoration: BoxDecoration(
                    color: isLast ? event.statusColor : Colors.transparent,
                    shape: BoxShape.circle,
                    border: Border.all(color: event.statusColor, width: 2),
                  ),
                ),
                if (index < events.length - 1)
                  Container(
                    width: 2,
                    height: 60,
                    color: AppColors.border,
                  ),
              ],
            ),
            const SizedBox(width: 12),
            // Contenido
            Expanded(
              child: Padding(
                padding: const EdgeInsets.only(bottom: 16),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Row(
                      children: [
                        Text(
                          event.statusLabel,
                          style: AppTextStyles.labelLarge.copyWith(
                            color: isLast ? event.statusColor : AppColors.textPrimary,
                          ),
                        ),
                        if (isLast) ...[
                          const SizedBox(width: 8),
                          Container(
                            padding: const EdgeInsets.symmetric(horizontal: 6, vertical: 2),
                            decoration: BoxDecoration(
                              color: AppColors.package,
                              borderRadius: BorderRadius.circular(4),
                            ),
                            child: Text('Ahora', style: AppTextStyles.labelSmall.copyWith(color: Colors.white)),
                          ),
                        ],
                      ],
                    ),
                    Text(event.description, style: AppTextStyles.bodySmall),
                    Text(event.formattedTime, style: AppTextStyles.labelSmall.copyWith(color: AppColors.textDisabled)),
                  ],
                ),
              ),
            ),
          ],
        );
      },
    );
  }
}