import 'package:flutter/material.dart';

import '../../core/theme/app_colors.dart';
import '../../core/theme/app_text_styles.dart';

/// Logo de EspinarGo reutilizable.
/// Muestra el ícono + el nombre de la app.
class EspinarGoLogo extends StatelessWidget {
  final String size;
  final Color? color;
  final bool showTagline;

  const EspinarGoLogo({
    super.key,
    this.size = 'medium',
    this.color,
    this.showTagline = false,
  });

  @override
  Widget build(BuildContext context) {
    final logoColor = color ?? Colors.white;
    final logoSize = _getLogoSize();
    final fontSize = _getFontSize();

    return Column(
      mainAxisSize: MainAxisSize.min,
      children: [
        Row(
          mainAxisSize: MainAxisSize.min,
          crossAxisAlignment: CrossAxisAlignment.center,
          children: [
            // Ícono triangular estilo pin/marker
            Container(
              width: logoSize,
              height: logoSize,
              decoration: BoxDecoration(
                color: logoColor,
                borderRadius: BorderRadius.circular(logoSize * 0.2),
              ),
              child: Center(
                child: Text(
                  'E',
                  style: TextStyle(
                    color: color != null ? AppColors.primary : Colors.white,
                    fontSize: logoSize * 0.5,
                    fontWeight: FontWeight.bold,
                  ),
                ),
              ),
            ),
            const SizedBox(width: 12),
            // Nombre de la app
            Text(
              'EspinarGo',
              style: AppTextStyles.displayLarge.copyWith(
                color: logoColor,
                fontSize: fontSize,
              ),
            ),
          ],
        ),
        if (showTagline) ...[
          const SizedBox(height: 4),
          Text(
            'Espinar · Cusco · Perú',
            style: TextStyle(
              color: logoColor.withOpacity(0.8),
              fontSize: fontSize * 0.5,
            ),
          ),
        ],
      ],
    );
  }

  double _getLogoSize() {
    switch (size) {
      case 'small':
        return 32;
      case 'large':
        return 64;
      default:
        return 48;
    }
  }

  double _getFontSize() {
    switch (size) {
      case 'small':
        return 18;
      case 'large':
        return 32;
      default:
        return 24;
    }
  }
}