import 'package:flutter/material.dart';
import 'package:flutter/services.dart';

import '../../../../core/theme/app_colors.dart';
import '../../../../core/theme/app_text_styles.dart';

/// Barra de búsqueda para rastrear paquetes.
class TrackingSearchBar extends StatelessWidget {
  final ValueChanged<String> onSearch;
  final bool isLoading;
  final String? initialValue;

  const TrackingSearchBar({
    super.key,
    required this.onSearch,
    this.isLoading = false,
    this.initialValue,
  });

  @override
  Widget build(BuildContext context) {
    final controller = TextEditingController(text: initialValue);

    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 12),
      decoration: BoxDecoration(
        color: Colors.white,
        borderRadius: BorderRadius.circular(16),
        border: Border.all(color: AppColors.package),
      ),
      child: Row(
        children: [
          const Icon(Icons.inventory_2, color: AppColors.package),
          const SizedBox(width: 12),
          Expanded(
            child: TextField(
              controller: controller,
              textCapitalization: TextCapitalization.characters,
              decoration: InputDecoration(
                hintText: 'ESP-YYYYMMDD-NNNN',
                hintStyle: AppTextStyles.bodyMedium.copyWith(color: AppColors.textDisabled),
                border: InputBorder.none,
              ),
              onSubmitted: (value) {
                if (value.length >= 8) onSearch(value);
              },
            ),
          ),
          if (isLoading)
            const SizedBox(
              width: 24,
              height: 24,
              child: CircularProgressIndicator(strokeWidth: 2),
            )
          else
            ElevatedButton(
              onPressed: () {
                if (controller.text.length >= 8) {
                  onSearch(controller.text);
                }
              },
              style: ElevatedButton.styleFrom(
                backgroundColor: AppColors.package,
                padding: const EdgeInsets.symmetric(horizontal: 16),
              ),
              child: const Text('Rastrear'),
            ),
        ],
      ),
    );
  }
}