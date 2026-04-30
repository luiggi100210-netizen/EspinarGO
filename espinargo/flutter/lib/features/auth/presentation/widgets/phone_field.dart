import 'package:flutter/material.dart';
import 'package:flutter/services.dart';

import '../../../../core/theme/app_colors.dart';
import '../../../../core/theme/app_text_styles.dart';

/// Campo especializado para números de teléfono peruano.
/// Muestra la bandera de Perú y el prefijo +51.
class PhoneField extends StatelessWidget {
  final TextEditingController controller;
  final String? Function(String?)? validator;
  final ValueChanged<String>? onChanged;
  final bool enabled;

  const PhoneField({
    super.key,
    required this.controller,
    this.validator,
    this.onChanged,
    this.enabled = true,
  });

  @override
  Widget build(BuildContext context) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Text(
          'Teléfono',
          style: AppTextStyles.labelMedium,
        ),
        const SizedBox(height: 8),
        TextFormField(
          controller: controller,
          enabled: enabled,
          keyboardType: TextInputType.phone,
          validator: validator,
          onChanged: onChanged,
          maxLength: 9,
          inputFormatters: [
            FilteringTextInputFormatter.digitsOnly,
          ],
          style: AppTextStyles.bodyMedium,
          decoration: InputDecoration(
            hintText: '987 654 321',
            hintStyle: AppTextStyles.bodyMedium.copyWith(
              color: AppColors.textDisabled,
            ),
            prefixIcon: Padding(
              padding: const EdgeInsets.only(left: 12, right: 8),
              child: Row(
                mainAxisSize: MainAxisSize.min,
                children: [
                  const Text(
                    '🇵🇪',
                    style: TextStyle(fontSize: 20),
                  ),
                  const SizedBox(width: 4),
                  const Text(
                    '+51',
                    style: TextStyle(
                      color: AppColors.textPrimary,
                      fontSize: 14,
                      fontWeight: FontWeight.w500,
                    ),
                  ),
                ],
              ),
            ),
            prefixIconConstraints: const BoxConstraints(
              minWidth: 90,
            ),
            filled: true,
            fillColor: AppColors.background,
            border: OutlineInputBorder(
              borderRadius: BorderRadius.circular(10),
              borderSide: const BorderSide(color: AppColors.border),
            ),
            focusedBorder: OutlineInputBorder(
              borderRadius: BorderRadius.circular(10),
              borderSide: const BorderSide(
                color: AppColors.primary,
                width: 1.5,
              ),
            ),
            errorBorder: OutlineInputBorder(
              borderRadius: BorderRadius.circular(10),
              borderSide: const BorderSide(color: AppColors.error),
            ),
            contentPadding: const EdgeInsets.symmetric(
              horizontal: 16,
              vertical: 14,
            ),
            counterText: '',
          ),
        ),
      ],
    );
  }

  /// Construye el número completo con prefijo.
  static String buildFullPhone(String digits) {
    if (digits.startsWith('+51')) {
      return digits;
    }
    if (digits.startsWith('9')) {
      return '+51$digits';
    }
    return digits;
  }
}