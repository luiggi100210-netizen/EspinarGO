import 'package:flutter/material.dart';
import 'package:flutter/services.dart';

import '../../../../core/theme/app_colors.dart';
import '../../../../core/theme/app_text_styles.dart';

/// Dialog de calificación que aparece al completar un viaje.
class RatingDialog extends StatefulWidget {
  final String driverName;
  final Function(int score, String? comment) onSubmit;
  final VoidCallback onSkip;

  const RatingDialog({
    super.key,
    required this.driverName,
    required this.onSubmit,
    required this.onSkip,
  });

  @override
  State<RatingDialog> createState() => _RatingDialogState();
}

class _RatingDialogState extends State<RatingDialog> {
  int _selectedRating = 0;
  final TextEditingController _commentController = TextEditingController();

  @override
  void dispose() {
    _commentController.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return Dialog(
      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(20)),
      child: Padding(
        padding: const EdgeInsets.all(24),
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            // Check icon
            Container(
              width: 64,
              height: 64,
              decoration: const BoxDecoration(
                color: AppColors.successLight,
                shape: BoxShape.circle,
              ),
              child: const Icon(
                Icons.check,
                color: AppColors.success,
                size: 32,
              ),
            ),
            const SizedBox(height: 16),

            // Title
            Text(
              '¡Llegaste a tu destino!',
              style: AppTextStyles.headingMedium,
            ),
            const SizedBox(height: 8),
            Text(
              '¿Cómo fue tu viaje con ${widget.driverName}?',
              style: AppTextStyles.bodyMedium.copyWith(
                color: AppColors.textSecondary,
              ),
              textAlign: TextAlign.center,
            ),
            const SizedBox(height: 24),

            // Stars
            Row(
              mainAxisAlignment: MainAxisAlignment.center,
              children: List.generate(5, (index) {
                final starIndex = index + 1;
                return GestureDetector(
                  onTap: () {
                    HapticFeedback.selectionClick();
                    setState(() => _selectedRating = starIndex);
                  },
                  child: Padding(
                    padding: const EdgeInsets.symmetric(horizontal: 4),
                    child: Icon(
                      starIndex <= _selectedRating
                          ? Icons.star
                          : Icons.star_border,
                      color: const Color(0xFFFBBC04),
                      size: 40,
                    ),
                  ),
                );
              }),
            ),
            const SizedBox(height: 16),

            // Comment field
            TextField(
              controller: _commentController,
              maxLength: 200,
              maxLines: 2,
              decoration: InputDecoration(
                hintText: 'Comentario opcional...',
                hintStyle: AppTextStyles.bodySmall,
                border: OutlineInputBorder(
                  borderRadius: BorderRadius.circular(12),
                  borderSide: const BorderSide(color: AppColors.border),
                ),
                contentPadding: const EdgeInsets.all(12),
              ),
            ),
            const SizedBox(height: 16),

            // Submit button
            SizedBox(
              width: double.infinity,
              child: ElevatedButton(
                onPressed: _selectedRating > 0
                    ? () => widget.onSubmit(
                          _selectedRating,
                          _commentController.text.isNotEmpty
                              ? _commentController.text
                              : null,
                        )
                    : null,
                child: const Text('Calificar'),
              ),
            ),
            const SizedBox(height: 8),

            // Skip button
            TextButton(
              onPressed: widget.onSkip,
              child: Text(
                'Omitir',
                style: AppTextStyles.labelMedium.copyWith(
                  color: AppColors.textSecondary,
                ),
              ),
            ),
          ],
        ),
      ),
    );
  }
}