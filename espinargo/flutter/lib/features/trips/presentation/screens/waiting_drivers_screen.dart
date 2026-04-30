import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import '../../../../core/theme/app_colors.dart';
import '../../../../core/theme/app_text_styles.dart';
import '../../domain/providers/trip_provider.dart';
import '../widgets/trip_info_card.dart';
import '../widgets/trip_status_bar.dart';

/// Pantalla de espera mientras los conductores ven la solicitud.
class WaitingDriversScreen extends ConsumerWidget {
  const WaitingDriversScreen({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final tripState = ref.watch(tripProvider).valueOrNull;

    if (tripState == null) {
      return const Scaffold(
        body: Center(child: CircularProgressIndicator()),
      );
    }

    // Si hay ofertas, navegar a la pantalla de ofertas
    if (tripState.offers.isNotEmpty) {
      WidgetsBinding.instance.addPostFrameCallback((_) {
        context.go('/trip-offers');
      });
    }

    return Scaffold(
      body: Stack(
        children: [
          // Mapa de fondo (simplificado)
          Container(
            color: AppColors.mapBackground,
            child: const Center(
              child: Column(
                mainAxisAlignment: MainAxisAlignment.center,
                children: [
                  // Animación de radar
                  SizedBox(
                    width: 120,
                    height: 120,
                    child: CircularProgressIndicator(
                      strokeWidth: 4,
                      valueColor: AlwaysStoppedAnimation(AppColors.primary),
                    ),
                  ),
                  SizedBox(height: 24),
                  Text(
                    '🛺',
                    style: TextStyle(fontSize: 64),
                  ),
                ],
              ),
            ),
          ),

          // Panel inferior
          DraggableScrollableSheet(
            initialChildSize: 0.5,
            minChildSize: 0.3,
            maxChildSize: 0.8,
            builder: (context, scrollController) {
              return Container(
                decoration: const BoxDecoration(
                  color: Colors.white,
                  borderRadius: BorderRadius.vertical(top: Radius.circular(20)),
                ),
                child: ListView(
                  controller: scrollController,
                  padding: const EdgeInsets.all(16),
                  children: [
                    // Indicador de arrastre
                    Center(
                      child: Container(
                        width: 40,
                        height: 4,
                        decoration: BoxDecoration(
                          color: AppColors.border,
                          borderRadius: BorderRadius.circular(2),
                        ),
                      ),
                    ),
                    const SizedBox(height: 16),

                    // Estado
                    TripStatusBar(
                      status: tripState.statusMessage,
                    ),
                    const SizedBox(height: 16),

                    // Info del viaje
                    if (tripState.currentTrip != null)
                      TripInfoCard(trip: tripState.currentTrip!),

                    const SizedBox(height: 16),

                    // Tu precio
                    Center(
                      child: Column(
                        children: [
                          Text(
                            'Tu precio',
                            style: AppTextStyles.labelMedium,
                          ),
                          Text(
                            tripState.currentTrip?.displayPrice ?? 'S/ 0.00',
                            style: AppTextStyles.priceDisplay,
                          ),
                        ],
                      ),
                    ),
                    const SizedBox(height: 16),

                    // Contador
                    Center(
                      child: Text(
                        'Buscando hace 1 min',
                        style: AppTextStyles.bodySmall,
                      ),
                    ),
                    const SizedBox(height: 24),

                    // Botón de cancelar
                    Center(
                      child: TextButton(
                        onPressed: () => _cancelTrip(context, ref),
                        child: Text(
                          'Cancelar búsqueda',
                          style: AppTextStyles.labelMedium.copyWith(
                            color: AppColors.error,
                          ),
                        ),
                      ),
                    ),
                  ],
                ),
              );
            },
          ),
        ],
      ),
    );
  }

  Future<void> _cancelTrip(BuildContext context, WidgetRef ref) async {
    final confirm = await showDialog<bool>(
      context: context,
      builder: (context) => AlertDialog(
        title: const Text('Cancelar búsqueda'),
        content: const Text('¿Estás seguro de que quieres cancelar la búsqueda?'),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(context, false),
            child: const Text('No'),
          ),
          TextButton(
            onPressed: () => Navigator.pop(context, true),
            child: Text('Sí, cancelar', style: TextStyle(color: AppColors.error)),
          ),
        ],
      ),
    );

    if (confirm == true) {
      await ref.read(tripProvider.notifier).cancelTrip();
      if (context.mounted) {
        context.go('/home');
      }
    }
  }
}