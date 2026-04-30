import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import 'package:google_maps_flutter/google_maps_flutter.dart';

import '../../../../core/theme/app_colors.dart';
import '../../../../core/theme/app_text_styles.dart';
import '../../../home/presentation/widgets/map_widget.dart';
import '../../domain/providers/trip_provider.dart';
import '../widgets/trip_info_card.dart';
import '../widgets/trip_status_bar.dart';

/// Pantalla del viaje en curso.
class TripActiveScreen extends ConsumerWidget {
  const TripActiveScreen({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final tripState = ref.watch(tripProvider).valueOrNull;
    final trip = tripState?.currentTrip;

    if (trip == null) {
      return const Scaffold(
        body: Center(child: CircularProgressIndicator()),
      );
    }

    // Navegar a completado cuando termine
    if (tripState?.flowStatus == TripFlowStatus.completed) {
      WidgetsBinding.instance.addPostFrameCallback((_) {
        context.go('/trip-completed');
      });
    }

    // Crear marcadores
    final markers = <Marker>{
      Marker(
        markerId: const MarkerId('origin'),
        position: trip.originLatLng,
        icon: BitmapDescriptor.defaultMarkerWithHue(BitmapDescriptor.hueGreen),
      ),
      Marker(
        markerId: const MarkerId('destination'),
        position: trip.destLatLng,
        icon: BitmapDescriptor.defaultMarkerWithHue(BitmapDescriptor.hueOrange),
      ),
    };

    // Agregar marcador del conductor si hay ubicación
    if (tripState?.driverLocation != null) {
      markers.add(Marker(
        markerId: const MarkerId('driver'),
        position: tripState!.driverLocation!,
        icon: BitmapDescriptor.defaultMarkerWithHue(BitmapDescriptor.hueBlue),
        infoWindow: const InfoWindow(title: 'Tu conductor'),
      ));
    }

    // Polilínea de la ruta
    final polylines = <Polyline>{
      Polyline(
        polylineId: const PolylineId('route'),
        points: [
          trip.originLatLng,
          trip.destLatLng,
        ],
        color: AppColors.info,
        width: 5,
      ),
    };

    return Scaffold(
      body: Stack(
        children: [
          // Mapa
          MapWidget(
            initialPosition: trip.originLatLng,
            markers: markers,
            polylines: polylines,
          ),

          // Status bar
          TripStatusBar(
            status: tripState?.statusMessage ?? '',
            driverName: trip.driver?.fullName,
            estimatedArrival: '~5 min',
          ),

          // Panel inferior
          Positioned(
            left: 0,
            right: 0,
            bottom: 0,
            child: Container(
              padding: const EdgeInsets.all(16),
              decoration: const BoxDecoration(
                color: Colors.white,
                borderRadius: BorderRadius.vertical(top: Radius.circular(20)),
              ),
              child: SafeArea(
                child: Column(
                  mainAxisSize: MainAxisSize.min,
                  children: [
                    // Info del conductor
                    if (trip.driver != null) ...[
                      Row(
                        children: [
                          CircleAvatar(
                            radius: 24,
                            backgroundColor: AppColors.primary,
                            child: Text(
                              trip.driver!.initials,
                              style: AppTextStyles.labelLarge.copyWith(
                                color: Colors.white,
                              ),
                            ),
                          ),
                          const SizedBox(width: 12),
                          Expanded(
                            child: Column(
                              crossAxisAlignment: CrossAxisAlignment.start,
                              children: [
                                Text(
                                  trip.driver!.fullName,
                                  style: AppTextStyles.labelLarge,
                                ),
                                Row(
                                  children: [
                                    const Icon(Icons.star, color: AppColors.warning, size: 16),
                                    const SizedBox(width: 4),
                                    Text('5.0 · 120 viajes', style: AppTextStyles.bodySmall),
                                  ],
                                ),
                              ],
                            ),
                          ),
                        ],
                      ),
                      const SizedBox(height: 16),
                      // Botones de contacto
                      Row(
                        children: [
                          Expanded(
                            child: OutlinedButton.icon(
                              onPressed: () {},
                              icon: const Icon(Icons.phone),
                              label: const Text('Llamar'),
                            ),
                          ),
                          const SizedBox(width: 12),
                          Expanded(
                            child: OutlinedButton.icon(
                              onPressed: () {},
                              icon: const Icon(Icons.chat),
                              label: const Text('WhatsApp'),
                            ),
                          ),
                        ],
                      ),
                      const SizedBox(height: 16),
                    ],

                    // Banner de llegada
                    if (tripState?.flowStatus == TripFlowStatus.driverArrived)
                      Container(
                        padding: const EdgeInsets.all(12),
                        decoration: BoxDecoration(
                          color: AppColors.successLight,
                          borderRadius: BorderRadius.circular(12),
                        ),
                        child: Row(
                          children: [
                            const Icon(Icons.location_on, color: AppColors.success),
                            const SizedBox(width: 8),
                            Text(
                              '¡Tu conductor está aquí!',
                              style: AppTextStyles.labelMedium.copyWith(
                                color: AppColors.success,
                              ),
                            ),
                          ],
                        ),
                      ),

                    // Info del viaje
                    TripInfoCard(trip: trip),

                    // Botón de cancelar (solo si no ha iniciado)
                    if (trip.status == 'accepted') ...[
                      const SizedBox(height: 12),
                      TextButton(
                        onPressed: () => _cancelTrip(context, ref),
                        child: Text(
                          'Cancelar viaje',
                          style: AppTextStyles.labelMedium.copyWith(
                            color: AppColors.error,
                          ),
                        ),
                      ),
                    ],
                  ],
                ),
              ),
            ),
          ),
        ],
      ),
    );
  }

  Future<void> _cancelTrip(BuildContext context, WidgetRef ref) async {
    final confirm = await showDialog<bool>(
      context: context,
      builder: (context) => AlertDialog(
        title: const Text('Cancelar viaje'),
        content: const Text('¿Estás seguro de que quieres cancelar el viaje?'),
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

// Importar el enum
import '../../domain/providers/trip_state.dart';