import 'package:flutter/material.dart';

import '../../../../core/theme/app_colors.dart';
import '../../../../core/theme/app_text_styles.dart';
import '../../../../shared/widgets/primary_button.dart';
import '../../domain/providers/map_provider.dart';
import 'service_selector.dart';

/// Panel inferior que se desliza hacia arriba.
/// Muestra el selector de servicio y el botón de acción.
class BottomSheetHome extends StatelessWidget {
  final MapState mapState;
  final VoidCallback onRequestTrip;
  final VoidCallback onClearRoute;

  const BottomSheetHome({
    super.key,
    required this.mapState,
    required this.onRequestTrip,
    required this.onClearRoute,
  });

  @override
  Widget build(BuildContext context) {
    final hasRoute = mapState.route != null;

    return AnimatedContainer(
      duration: const Duration(milliseconds: 300),
      height: hasRoute ? 280 : 180,
      decoration: const BoxDecoration(
        color: Colors.white,
        borderRadius: BorderRadius.vertical(top: Radius.circular(20)),
        boxShadow: [
          BoxShadow(
            color: Colors.black12,
            blurRadius: 10,
            offset: Offset(0, -2),
          ),
        ],
      ),
      child: Column(
        children: [
          // Indicador de arrastre
          Container(
            margin: const EdgeInsets.only(top: 12),
            width: 40,
            height: 4,
            decoration: BoxDecoration(
              color: AppColors.border,
              borderRadius: BorderRadius.circular(2),
            ),
          ),
          const SizedBox(height: 16),
          // Contenido
          Expanded(
            child: hasRoute ? _buildRouteContent() : _buildIdleContent(),
          ),
        ],
      ),
    );
  }

  /// Contenido cuando NO hay ruta seleccionada.
  Widget _buildIdleContent() {
    return Column(
      children: [
        Padding(
          padding: const EdgeInsets.symmetric(horizontal: 16),
          child: Text(
            '¿Qué necesitas hoy?',
            style: AppTextStyles.headingMedium,
          ),
        ),
        const SizedBox(height: 16),
        ServiceSelector(
          selectedService: mapState.selectedService,
          onServiceSelected: (service) {},
        ),
        const Spacer(),
      ],
    );
  }

  /// Contenido cuando hay ruta seleccionada.
  Widget _buildRouteContent() {
    final route = mapState.route;

    return Padding(
      padding: const EdgeInsets.symmetric(horizontal: 16),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          // Resumen de la ruta
          Row(
            children: [
              // Punto de origen
              Expanded(
                child: Row(
                  children: [
                    Container(
                      width: 8,
                      height: 8,
                      decoration: const BoxDecoration(
                        color: AppColors.success,
                        shape: BoxShape.circle,
                      ),
                    ),
                    const SizedBox(width: 12),
                    Expanded(
                      child: Text(
                        mapState.origin?.name ?? 'Origen',
                        style: AppTextStyles.bodyMedium,
                        maxLines: 1,
                        overflow: TextOverflow.ellipsis,
                      ),
                    ),
                  ],
                ),
              ),
            ],
          ),
          const SizedBox(height: 8),
          // Punto de destino
          Row(
            children: [
              Container(
                width: 8,
                height: 8,
                decoration: const BoxDecoration(
                  color: AppColors.primary,
                  shape: BoxShape.circle,
                ),
              ),
              const SizedBox(width: 12),
              Expanded(
                child: Text(
                  mapState.destination?.name ?? 'Destino',
                  style: AppTextStyles.bodyMedium,
                  maxLines: 1,
                  overflow: TextOverflow.ellipsis,
                ),
              ),
            ],
          ),
          const SizedBox(height: 12),
          // Distancia y tiempo
          Row(
            children: [
              Text(
                route?.formattedDistance ?? '',
                style: AppTextStyles.labelMedium.copyWith(
                  color: AppColors.textSecondary,
                ),
              ),
              const SizedBox(width: 8),
              Text(
                '•',
                style: TextStyle(color: AppColors.textDisabled),
              ),
              const SizedBox(width: 8),
              Text(
                route?.formattedDuration ?? '',
                style: AppTextStyles.labelMedium.copyWith(
                  color: AppColors.textSecondary,
                ),
              ),
            ],
          ),
          const SizedBox(height: 16),
          // Precio sugerido
          Row(
            mainAxisAlignment: MainAxisAlignment.spaceBetween,
            children: [
              Text(
                'Precio sugerido',
                style: AppTextStyles.bodyMedium,
              ),
              Text(
                route?.suggestedPriceFormatted ?? 'S/ 0.00',
                style: AppTextStyles.priceMedium,
              ),
            ],
          ),
          const Spacer(),
          // Botón
          PrimaryButton(
            text: 'Ver conductores disponibles',
            onPressed: onRequestTrip,
            isLoading: mapState.isLoadingRoute,
          ),
          const SizedBox(height: 8),
          // Botón de cancelar
          Center(
            child: TextButton(
              onPressed: onClearRoute,
              child: Text(
                'Cambiar destino',
                style: AppTextStyles.labelMedium.copyWith(
                  color: AppColors.primary,
                ),
              ),
            ),
          ),
        ],
      ),
    );
  }
}