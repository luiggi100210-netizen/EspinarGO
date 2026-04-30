import 'package:flutter/material.dart';

import '../../../../core/theme/app_colors.dart';
import '../../../../core/theme/app_text_styles.dart';

/// Selector de tamaño de paquete.
class PackageSizeSelector extends StatelessWidget {
  final String? selectedSize;
  final ValueChanged<String> onSizeSelected;

  const PackageSizeSelector({
    super.key,
    this.selectedSize,
    required this.onSizeSelected,
  });

  static const List<Map<String, dynamic>> _sizes = [
    {'id': 'envelope', 'emoji': '✉️', 'title': 'Sobre', 'subtitle': 'Documentos, cartas', 'maxWeight': 'Hasta 500g'},
    {'id': 'small', 'emoji': '📦', 'title': 'Pequeño', 'subtitle': 'Zapatos, libros', 'maxWeight': 'Hasta 5kg'},
    {'id': 'medium', 'emoji': '🗃️', 'title': 'Mediano', 'subtitle': 'Ropa, electrodomésticos', 'maxWeight': 'Hasta 15kg'},
    {'id': 'large', 'emoji': '📫', 'title': 'Grande', 'subtitle': 'Muebles pequeños', 'maxWeight': 'Hasta 30kg'},
  ];

  @override
  Widget build(BuildContext context) {
    return GridView.builder(
      shrinkWrap: true,
      physics: const NeverScrollableScrollPhysics(),
      gridDelegate: const SliverGridDelegateWithFixedCrossAxisCount(
        crossAxisCount: 2,
        childAspectRatio: 1.2,
        crossAxisSpacing: 12,
        mainAxisSpacing: 12,
      ),
      itemCount: _sizes.length,
      itemBuilder: (context, index) {
        final size = _sizes[index];
        final isSelected = selectedSize == size['id'];

        return GestureDetector(
          onTap: () => onSizeSelected(size['id'] as String),
          child: AnimatedContainer(
            duration: const Duration(milliseconds: 200),
            padding: const EdgeInsets.all(12),
            decoration: BoxDecoration(
              color: isSelected ? AppColors.packageLight : Colors.white,
              borderRadius: BorderRadius.circular(16),
              border: Border.all(
                color: isSelected ? AppColors.package : AppColors.border,
                width: isSelected ? 2 : 1,
              ),
            ),
            child: Column(
              mainAxisAlignment: MainAxisAlignment.center,
              children: [
                Text(size['emoji'] as String, style: const TextStyle(fontSize: 32)),
                const SizedBox(height: 4),
                Text(size['title'] as String, style: AppTextStyles.labelLarge),
                Text(size['subtitle'] as String, style: AppTextStyles.bodySmall, textAlign: TextAlign.center),
                const SizedBox(height: 2),
                Text(size['maxWeight'] as String, style: AppTextStyles.labelSmall.copyWith(color: AppColors.package)),
              ],
            ),
          ),
        );
      },
    );
  }
}