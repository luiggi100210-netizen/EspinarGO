import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import 'package:google_maps_flutter/google_maps_flutter.dart';

import '../../../../core/theme/app_colors.dart';
import '../../../../core/theme/app_text_styles.dart';
import '../../../../shared/widgets/primary_button.dart';
import '../../../trips/presentation/widgets/trip_status_bar.dart';
import '../../domain/providers/driver_provider.dart';
import '../widgets/passenger_info_card.dart';

/// Pantalla del viaje activo desde la perspectiva del conductor.
class DriverTripActiveScreen extends ConsumerWidget {
  const DriverTripActiveScreen({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final driverState = ref.watch(driverProvider).valueOrNull;
    final trip = driverState?.currentTrip;
    final status = driverState?.flowStatus ?? DriverFlowStatus.goingToPassenger;

    if (trip == null) {
      return const Scaffold(
        body: Center(child: CircularProgressIndicator()),
      );
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

    return Scaffold(
      body: Stack(
        children: [
          // Mapa
          GoogleMap(
            initialCameraPosition: CameraPosition(
              target: trip.originLatLng,
              zoom: 15,
            ),
            markers: markers,
            myLocationEnabled: true,
            myLocationButtonEnabled: false,
            zoomControlsEnabled: false,
          ),

          // Status bar
          TripStatusBar(
            status: driverState?.statusMessage ?? '',
            driverName: trip.passenger?.fullName,
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
                    if (status == DriverFlowStatus.offerAccepted ||
                        status == DriverFlowStatus.goingToPassenger) ...[
                      if (trip.passenger != null)
                        PassengerInfoCard(
                          passenger: trip.passenger!,
                          trip: trip,
                          onCallPassenger: () {},
                          onWhatsAppPassenger: () {},
                        ),
                      const SizedBox(height: 16),
                      Text(
                        status == DriverFlowStatus.offerAccepted
                            ? 'En camino al pasajero'
                            : 'Recogiendo al pasajero',
                        style: AppTextStyles.labelMedium,
                      ),
                      const SizedBox(height: 16),
                      PrimaryButton(
                        text: 'El pasajero ya está conmigo',
                        onPressed: () async {
                          final success = await ref
                              .read(driverProvider.notifier)
                              .startTrip(trip.id);
                          if (success && context.mounted) {
                            context.go('/driver/trip-active');
                          }
                        },
                      ),
                    ],

                    if (status == DriverFlowStatus.passengerOnboard) ...[
                      TripInfoCard(trip: trip),
                      const SizedBox(height: 16),
                      PrimaryButton(
                        text: 'Llegué al destino',
                        onPressed: () async {
                          final success = await ref
                              .read(driverProvider.notifier)
                              .completeTrip(trip.id);
                          if (success && context.mounted) {
                            context.go('/driver/trip-completed');
                          }
                        },
                      ),
                    ],

                    const SizedBox(height: 12),
                    TextButton(
                      onPressed: () async {
                        final confirm = await showDialog<bool>(
                          context: context,
                          builder: (context) => AlertDialog(
                            title: const Text('Cancelar viaje'),
                            content: const Text(
                                '¿Estás seguro de que quieres cancelar?'),
                            actions: [
                              TextButton(
                                onPressed: () => Navigator.pop(context, false),
                                child: const Text('No'),
                              ),
                              TextButton(
                                onPressed: () => Navigator.pop(context, true),
                                child: Text('Sí, cancelar',
                                    style: TextStyle(color: AppColors.error)),
                              ),
                            ],
                          ),
                        );

                        if (confirm == true) {
                          await ref
                              .read(driverProvider.notifier)
                              .cancelTrip(trip.id);
                          if (context.mounted) {
                            context.go('/driver/dashboard');
                          }
                        }
                      },
                      child: Text(
                        'Cancelar viaje',
                        style: AppTextStyles.labelMedium.copyWith(
                          color: AppColors.error,
                        ),
                      ),
                    ),
                  ],
                ),
              ),
            ),
          ),
        ],
      ),
    );
  }
}