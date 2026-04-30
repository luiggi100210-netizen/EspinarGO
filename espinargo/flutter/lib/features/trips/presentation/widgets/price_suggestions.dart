import 'package:flutter/material.dart';

import '../../../../core/theme/app_colors.dart';
import '../../../../core/theme/app_text_styles.dart';
import '../../../../core/utils/formatters.dart';

/// Chips de precios sugeridos para selección rápida.
class PriceSuggestions extends StatelessWidget {
  final double suggestedPrice;
  final ValueChanged<double> onPriceSelected;
  final double? selectedPrice;

  const PriceSuggestions({
    super.key,
    required this.suggestedPrice,
    required this.onPriceSelected,
    this.selectedPrice,
  });

  @override
  Widget build(BuildContext context) {
    final prices = [
      (suggestedPrice * 0.8).roundToDouble(),
      suggestedPrice,
      (suggestedPrice * 1.2).roundToDouble(),
    ];

    final labels = ['Económico', 'Sugerido', 'Rápido'];

    return Row(
      children: List.generate(prices.length, (index) {
        final price = prices[index];
        final label = labels[index];
        final isSelected = selectedPrice == price;
        final isSuggested = index == 1;

        return Expanded(
          child: Padding(
            padding: EdgeInsets.only(right: index < 2 ? 8 : 0),
            child: GestureDetector(
              onTap: () => onPriceSelected(price),
              child: AnimatedContainer(
                duration: const Duration(milliseconds: 200),
                padding: const EdgeInsets.symmetric(vertical: 12),
                decoration: BoxDecoration(
                  color: isSelected ? AppColors.primary : Colors.white,
                  borderRadius: BorderRadius.circular(12),
                  border: Border.all(
                    color: isSelected ? AppColors.primary : AppColors.border,
                    width: isSelected ? 2 : 1,
                  ),
                ),
                child: Column(
                  children: [
                    if (isSuggested) ...[
                      const Text('⭐', style: TextStyle(fontSize: 14)),
                      const SizedBox(height: 4),
                    ],
                    Text(
                      label,
                      style: AppTextStyles.labelSmall.copyWith(
                        color: isSelected ? Colors.white : AppColors.textSecondary,
                      ),
                    ),
                    const SizedBox(height: 4),
                    Text(
                      Formatters.currency(price),
                      style: AppTextStyles.labelLarge.copyWith(
                        color: isSelected ? Colors.white : AppColors.textPrimary,
                        fontWeight: FontWeight.bold,
                      ),
                    ),
                  ],
                ),
              ),
            ),
          ),
        );
      }),
    );
  }
}