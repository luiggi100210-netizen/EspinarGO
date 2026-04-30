import 'package:flutter/material.dart';

import '../../../../core/theme/app_colors.dart';
import '../../../../core/theme/app_text_styles.dart';

/// Barra de búsqueda que aparece en la parte superior del mapa.
/// Al tocarla navega a la pantalla de búsqueda de destino.
class SearchBarWidget extends StatelessWidget {
  final VoidCallback onTap;
  final String? currentOriginName;

  const SearchBarWidget({
    super.key,
    required this.onTap,
    this.currentOriginName,
  });

  @override
  Widget build(BuildContext context) {
    return GestureDetector(
      onTap: onTap,
      child: Container(
        height: 52,
        decoration: BoxDecoration(
          color: Colors.white,
          borderRadius: BorderRadius.circular(12),
          boxShadow: [
            BoxShadow(
              color: Colors.black.withOpacity(0.08),
              blurRadius: 8,
              offset: const Offset(0, 2),
            ),
          ],
        ),
        child: Row(
          children: [
            const SizedBox(width: 12),
            // Ícono de punto de ubicación
            Container(
              width: 8,
              height: 8,
              decoration: const BoxDecoration(
                color: AppColors.success,
                shape: BoxShape.circle,
              ),
            ),
            const SizedBox(width: 12),
            // Texto de búsqueda
            Expanded(
              child: Text(
                currentOriginName ?? '¿A dónde vas?',
                style: currentOriginName != null
                    ? AppTextStyles.bodyMedium
                    : AppTextStyles.bodyMedium.copyWith(
                        color: AppColors.textDisabled,
                      ),
                maxLines: 1,
                overflow: TextOverflow.ellipsis,
              ),
            ),
            // Ícono de búsqueda
            const Padding(
              padding: EdgeInsets.symmetric(horizontal: 12),
              child: Icon(
                Icons.search,
                color: AppColors.textSecondary,
                size: 24,
              ),
            ),
          ],
        ),
      ),
    );
  }
}