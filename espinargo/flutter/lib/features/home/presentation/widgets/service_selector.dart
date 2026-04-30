import 'package:flutter/material.dart';

import '../../../../core/theme/app_colors.dart';
import '../../../../core/theme/app_text_styles.dart';

/// Selector horizontal de tipo de servicio.
/// Permite elegir entre Mototaxi, Auto o Encomienda.
class ServiceSelector extends StatelessWidget {
  final String selectedService;
  final Function(String) onServiceSelected;

  const ServiceSelector({
    super.key,
    required this.selectedService,
    required this.onServiceSelected,
  });

  static const List<Map<String, dynamic>> _services = [
    {
      'id': 'mototaxi',
      'icon': '🛺',
      'label': 'Mototaxi',
      'color': AppColors.primary,
    },
    {
      'id': 'car',
      'icon': '🚗',
      'label': 'Auto',
      'color': AppColors.info,
    },
    {
      'id': 'package',
      'icon': '📦',
      'label': 'Encomienda',
      'color': AppColors.package,
    },
  ];

  @override
  Widget build(BuildContext context) {
    return SingleChildScrollView(
      scrollDirection: Axis.horizontal,
      padding: const EdgeInsets.symmetric(horizontal: 16),
      child: Row(
        children: _services.map((service) {
          final isSelected = selectedService == service['id'];
          return Padding(
            padding: const EdgeInsets.only(right: 12),
            child: _ServiceChip(
              service: service,
              isSelected: isSelected,
              onTap: () => onServiceSelected(service['id'] as String),
            ),
          );
        }).toList(),
      ),
    );
  }
}

class _ServiceChip extends StatelessWidget {
  final Map<String, dynamic> service;
  final bool isSelected;
  final VoidCallback onTap;

  const _ServiceChip({
    required this.service,
    required this.isSelected,
    required this.onTap,
  });

  @override
  Widget build(BuildContext context) {
    final color = service['color'] as Color;

    return GestureDetector(
      onTap: onTap,
      child: AnimatedContainer(
        duration: const Duration(milliseconds: 200),
        height: 44,
        padding: const EdgeInsets.symmetric(horizontal: 16),
        decoration: BoxDecoration(
          color: isSelected ? color.withOpacity(0.1) : Colors.white,
          borderRadius: BorderRadius.circular(22),
          border: Border.all(
            color: isSelected ? color : AppColors.border,
            width: isSelected ? 2 : 1,
          ),
        ),
        child: Row(
          mainAxisSize: MainAxisSize.min,
          children: [
            Text(
              service['icon'] as String,
              style: const TextStyle(fontSize: 20),
            ),
            const SizedBox(width: 8),
            Text(
              service['label'] as String,
              style: AppTextStyles.labelLarge.copyWith(
                color: isSelected ? color : AppColors.textSecondary,
                fontWeight: isSelected ? FontWeight.w600 : FontWeight.w500,
              ),
            ),
          ],
        ),
      ),
    );
  }
}