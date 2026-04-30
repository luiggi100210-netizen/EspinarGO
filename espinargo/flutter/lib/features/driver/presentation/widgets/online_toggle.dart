import 'package:flutter/material.dart';

import '../../../../core/theme/app_colors.dart';
import '../../../../core/theme/app_text_styles.dart';

/// Toggle para activar/desactivar modo online.
class OnlineToggle extends StatelessWidget {
  final bool isOnline;
  final bool isLoading;
  final VoidCallback onToggle;

  const OnlineToggle({
    super.key,
    required this.isOnline,
    this.isLoading = false,
    required this.onToggle,
  });

  @override
  Widget build(BuildContext context) {
    return GestureDetector(
      onTap: isLoading
          ? null
          : () async {
              if (isOnline) {
                final confirm = await showDialog<bool>(
                  context: context,
                  builder: (context) => AlertDialog(
                    title: const Text('Desconectarse'),
                    content: const Text('¿Seguro que quieres desconectarte?'),
                    actions: [
                      TextButton(
                        onPressed: () => Navigator.pop(context, false),
                        child: const Text('Cancelar'),
                      ),
                      TextButton(
                        onPressed: () => Navigator.pop(context, true),
                        child: Text('Sí, desconectarme',
                            style: TextStyle(color: AppColors.error)),
                      ),
                    ],
                  ),
                );
                if (confirm == true) onToggle();
              } else {
                onToggle();
              }
            },
      child: AnimatedContainer(
        duration: const Duration(milliseconds: 300),
        height: 80,
        decoration: BoxDecoration(
          color: isOnline ? AppColors.primary : AppColors.background,
          borderRadius: BorderRadius.circular(16),
          border: Border.all(
            color: isOnline ? AppColors.primary : AppColors.border,
            width: 2,
          ),
        ),
        child: Center(
          child: isLoading
              ? const CircularProgressIndicator(color: Colors.white)
              : Row(
                  mainAxisAlignment: MainAxisAlignment.center,
                  children: [
                    Icon(
                      isOnline ? Icons.wifi : Icons.power_settings_new,
                      color: isOnline ? Colors.white : AppColors.textSecondary,
                      size: 28,
                    ),
                    const SizedBox(width: 12),
                    Column(
                      mainAxisAlignment: MainAxisAlignment.center,
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Text(
                          isOnline ? 'EN LÍNEA' : 'DESCONECTADO',
                          style: AppTextStyles.labelLarge.copyWith(
                            color: isOnline ? Colors.white : AppColors.textPrimary,
                            fontWeight: FontWeight.bold,
                          ),
                        ),
                        Text(
                          isOnline
                              ? 'Recibiendo solicitudes'
                              : 'Toca para empezar a recibir',
                          style: AppTextStyles.labelSmall.copyWith(
                            color: isOnline
                                ? Colors.white.withOpacity(0.8)
                                : AppColors.textSecondary,
                          ),
                        ),
                      ],
                    ),
                  ],
                ),
        ),
      ),
    );
  }
}