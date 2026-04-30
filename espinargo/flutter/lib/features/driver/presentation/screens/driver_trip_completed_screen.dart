import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import '../../../../core/theme/app_colors.dart';
import '../../../../core/theme/app_text_styles.dart';
import '../../../../core/utils/formatters.dart';
import '../../../../shared/widgets/primary_button.dart';
import '../../domain/providers/driver_provider.dart';
import '../../../trips/presentation/widgets/rating_dialog.dart';

/// Pantalla de resumen tras completar un viaje.
class DriverTripCompletedScreen extends ConsumerStatefulWidget {
  const DriverTripCompletedScreen({super.key});

  @override
  ConsumerState<DriverTripCompletedScreen> createState() => _DriverTripCompletedScreenState();
}

class _DriverTripCompletedScreenState extends ConsumerState<DriverTripCompletedScreen> {
  @override
  void initState() {
    super.initState();
    Future.delayed(const Duration(seconds: 1), () {
      if (mounted) _showRatingDialog();
    });
  }

  void _showRatingDialog() {
    showDialog(
      context: context,
      barrierDismissible: false,
      builder: (context) => RatingDialog(
        driverName: 'Pasajero',
        onSubmit: (score, comment) {
          Navigator.pop(context);
        },
        onSkip: () => Navigator.pop(context),
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    final driverState = ref.watch(driverProvider).valueOrNull;
    final trip = driverState?.currentTrip;
    final price = double.tryParse(trip?.finalPrice ?? trip?.proposedPrice ?? '0') ?? 0;

    return Scaffold(
      backgroundColor: AppColors.background,
      body: SafeArea(
        child: Padding(
          padding: const EdgeInsets.all(24),
          child: Column(
            children: [
              const Spacer(),
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
              Text(
                '¡Viaje completado!',
                style: AppTextStyles.headingLarge,
              ),
              const SizedBox(height: 8),
              Text(
                'Has ganado ${Formatters.currency(price)} por este viaje',
                style: AppTextStyles.bodyMedium.copyWith(
                  color: AppColors.textSecondary,
                ),
              ),
              const Spacer(),

              // Ganancias acumuladas
              Container(
                padding: const EdgeInsets.all(16),
                decoration: BoxDecoration(
                  color: AppColors.primaryLight,
                  borderRadius: BorderRadius.circular(16),
                ),
                child: Row(
                  mainAxisAlignment: MainAxisAlignment.spaceBetween,
                  children: [
                    Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Text('Hoy', style: AppTextStyles.labelMedium),
                        Text(
                          Formatters.currency(driverState?.todayEarnings ?? 0),
                          style: AppTextStyles.priceMedium,
                        ),
                      ],
                    ),
                    Column(
                      crossAxisAlignment: CrossAxisAlignment.end,
                      children: [
                        Text('Viajes', style: AppTextStyles.labelMedium),
                        Text(
                          '${driverState?.todayTrips ?? 0}',
                          style: AppTextStyles.priceMedium,
                        ),
                      ],
                    ),
                  ],
                ),
              ),
              const SizedBox(height: 32),

              PrimaryButton(
                text: 'Volver al mapa',
                onPressed: () {
                  ref.read(driverProvider.notifier).resetState();
                  context.go('/driver/dashboard');
                },
              ),
              const SizedBox(height: 12),
              TextButton(
                onPressed: () => context.go('/driver/earnings'),
                child: Text(
                  'Ver mis ganancias',
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