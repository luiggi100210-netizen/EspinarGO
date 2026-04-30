import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../../../core/theme/app_colors.dart';
import '../../../../core/theme/app_text_styles.dart';
import '../../../../core/utils/formatters.dart';
import '../../domain/providers/driver_provider.dart';

/// Pantalla de ganancias del conductor.
class DriverEarningsScreen extends ConsumerStatefulWidget {
  const DriverEarningsScreen({super.key});

  @override
  ConsumerState<DriverEarningsScreen> createState() => _DriverEarningsScreenState();
}

class _DriverEarningsScreenState extends ConsumerState<DriverEarningsScreen> {
  @override
  void initState() {
    super.initState();
    WidgetsBinding.instance.addPostFrameCallback((_) {
      ref.read(driverProvider.notifier).loadEarnings();
    });
  }

  @override
  Widget build(BuildContext context) {
    final driverState = ref.watch(driverProvider).valueOrNull;

    return Scaffold(
      appBar: AppBar(
        title: const Text('Mis ganancias'),
        backgroundColor: Colors.transparent,
        elevation: 0,
      ),
      body: driverState == null
          ? const Center(child: CircularProgressIndicator())
          : RefreshIndicator(
              onRefresh: () async {
                await ref.read(driverProvider.notifier).loadEarnings();
              },
              child: SingleChildScrollView(
                physics: const AlwaysScrollableScrollPhysics(),
                padding: const EdgeInsets.all(16),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    // Total
                    Container(
                      width: double.infinity,
                      padding: const EdgeInsets.all(24),
                      decoration: BoxDecoration(
                        gradient: LinearGradient(
                          colors: [AppColors.primary, AppColors.primaryDark],
                          begin: Alignment.topLeft,
                          end: Alignment.bottomRight,
                        ),
                        borderRadius: BorderRadius.circular(20),
                      ),
                      child: Column(
                        children: [
                          Text(
                            'Ganancias de hoy',
                            style: AppTextStyles.labelMedium.copyWith(
                              color: Colors.white70,
                            ),
                          ),
                          const SizedBox(height: 8),
                          Text(
                            Formatters.currency(driverState.todayEarnings),
                            style: AppTextStyles.displayLarge.copyWith(
                              color: Colors.white,
                            ),
                          ),
                          const SizedBox(height: 8),
                          Text(
                            '${driverState.todayTrips} viajes completados',
                            style: AppTextStyles.bodyMedium.copyWith(
                              color: Colors.white70,
                            ),
                          ),
                        ],
                      ),
                    ),
                    const SizedBox(height: 24),

                    // Stats
                    Text('Estadísticas', style: AppTextStyles.headingSmall),
                    const SizedBox(height: 12),
                    _buildStatCard(
                      'Promedio por viaje',
                      Formatters.currency(
                        driverState.todayTrips > 0
                            ? driverState.todayEarnings / driverState.todayTrips
                            : 0,
                      ),
                    ),
                    _buildStatCard(
                      'Viajes hoy',
                      driverState.todayTrips.toString(),
                    ),
                    _buildStatCard(
                      'Calificación',
                      '4.8 ★',
                    ),
                    _buildStatCard(
                      'Tasa de aceptación',
                      '85%',
                    ),
                  ],
                ),
              ),
            ),
    );
  }

  Widget _buildStatCard(String label, String value) {
    return Container(
      margin: const EdgeInsets.only(bottom: 12),
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        color: Colors.white,
        borderRadius: BorderRadius.circular(12),
        border: Border.all(color: AppColors.border),
      ),
      child: Row(
        mainAxisAlignment: MainAxisAlignment.spaceBetween,
        children: [
          Text(label, style: AppTextStyles.bodyMedium),
          Text(value, style: AppTextStyles.labelLarge),
        ],
      ),
    );
  }
}