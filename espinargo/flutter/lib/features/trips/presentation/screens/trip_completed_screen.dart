import 'dart:async';

import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import '../../../../core/theme/app_colors.dart';
import '../../../../core/theme/app_text_styles.dart';
import '../../../../shared/widgets/primary_button.dart';
import '../../../ratings/domain/providers/rating_provider.dart';
import '../../domain/providers/trip_provider.dart';
import '../widgets/trip_info_card.dart';
import '../widgets/rating_dialog.dart';

/// Pantalla de resumen tras completar el viaje.
class TripCompletedScreen extends ConsumerStatefulWidget {
  const TripCompletedScreen({super.key});

  @override
  ConsumerState<TripCompletedScreen> createState() => _TripCompletedScreenState();
}

class _TripCompletedScreenState extends ConsumerState<TripCompletedScreen> {
  @override
  void initState() {
    super.initState();
    // Mostrar dialog de calificación después de 1 segundo
    Timer(const Duration(seconds: 1), () {
      _showRatingDialog();
    });
  }

  void _showRatingDialog() {
    final tripState = ref.read(tripProvider).valueOrNull;
    final driverName = tripState?.currentTrip?.driver?.fullName ?? 'Conductor';

    showDialog(
      context: context,
      barrierDismissible: false,
      builder: (context) => RatingDialog(
        driverName: driverName,
        onSubmit: (score, comment) async {
          Navigator.pop(context);
          final tripId = ref.read(tripProvider).valueOrNull?.currentTrip?.id;
          if (tripId == null) return;
          try {
            await ref.read(ratingRepositoryProvider).createRating(
              tripId: tripId,
              score: score,
              comment: comment,
            );
          } catch (_) {
            // La calificación es opcional; un error no bloquea el flujo
          }
        },
        onSkip: () {
          Navigator.pop(context);
        },
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    final tripState = ref.watch(tripProvider).valueOrNull;
    final trip = tripState?.currentTrip;

    return Scaffold(
      backgroundColor: AppColors.background,
      body: SafeArea(
        child: Padding(
          padding: const EdgeInsets.all(24),
          child: Column(
            children: [
              const Spacer(),

              // Check icon con animación
              Container(
                width: 100,
                height: 100,
                decoration: const BoxDecoration(
                  color: AppColors.successLight,
                  shape: BoxShape.circle,
                ),
                child: const Icon(
                  Icons.check,
                  color: AppColors.success,
                  size: 64,
                ),
              ),
              const SizedBox(height: 24),

              // Título
              Text(
                '¡Llegaste a tu destino!',
                style: AppTextStyles.headingLarge,
                textAlign: TextAlign.center,
              ),
              const SizedBox(height: 8),

              // Destino
              if (trip != null)
                Text(
                  trip.destAddress,
                  style: AppTextStyles.bodyMedium.copyWith(
                    color: AppColors.textSecondary,
                  ),
                  textAlign: TextAlign.center,
                ),
              const SizedBox(height: 32),

              // Resumen del viaje
              if (trip != null)
                TripInfoCard(trip: trip),

              const Spacer(),

              // Botón volver al inicio
              PrimaryButton(
                text: 'Volver al inicio',
                onPressed: () {
                  ref.read(tripProvider.notifier).resetTrip();
                  context.go('/home');
                },
              ),
              const SizedBox(height: 12),

              // Ver historial
              TextButton(
                onPressed: () => context.go('/trips/history'),
                child: Text(
                  'Ver historial de viajes',
                  style: AppTextStyles.labelMedium.copyWith(
                    color: AppColors.primary,
                  ),
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }
}