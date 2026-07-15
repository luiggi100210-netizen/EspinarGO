import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import '../../../../core/theme/app_colors.dart';
import '../../../../core/theme/app_text_styles.dart';
import '../../domain/providers/driver_provider.dart';
import '../../domain/providers/driver_state.dart';
import '../widgets/online_toggle.dart';
import '../widgets/trip_request_card.dart';
import '../widgets/earnings_summary_card.dart';
import '../widgets/driver_stats_row.dart';
import '../widgets/make_offer_sheet.dart';

/// Pantalla principal del conductor.
class DriverDashboardScreen extends ConsumerStatefulWidget {
  const DriverDashboardScreen({super.key});

  @override
  ConsumerState<DriverDashboardScreen> createState() =>
      _DriverDashboardScreenState();
}

class _DriverDashboardScreenState extends ConsumerState<DriverDashboardScreen> {
  @override
  Widget build(BuildContext context) {
    ref.listen<AsyncValue<DriverState>>(driverProvider, (previous, next) {
      final status = next.valueOrNull?.flowStatus;
      if (status == DriverFlowStatus.offerAccepted ||
          status == DriverFlowStatus.passengerOnboard) {
        context.go('/driver/trip-active');
      }
    });

    final driverState = ref.watch(driverProvider).valueOrNull;

    if (driverState == null) {
      return const Scaffold(
        body: Center(child: CircularProgressIndicator()),
      );
    }

    final isOnline = driverState.isOnline;
    final profile = driverState.driverProfile;

    return Scaffold(
      body: Stack(
        children: [
          // Mapa de fondo (simplificado)
          Container(color: AppColors.mapBackground),

          // Panel superior
          SafeArea(
            child: Padding(
              padding: const EdgeInsets.all(16),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  // Header
                  Row(
                    children: [
                      CircleAvatar(
                        radius: 20,
                        backgroundColor: AppColors.primary,
                        child: Text(
                          profile?.vehicleTypeLabel.substring(0, 1) ?? '?',
                          style: AppTextStyles.labelLarge.copyWith(color: Colors.white),
                        ),
                      ),
                      const SizedBox(width: 12),
                      Expanded(
                        child: Column(
                          crossAxisAlignment: CrossAxisAlignment.start,
                          children: [
                            Text('Conductor', style: AppTextStyles.labelMedium),
                            Text(
                              profile?.vehicleDescription ?? 'EspinarGo',
                              style: AppTextStyles.bodySmall,
                            ),
                          ],
                        ),
                      ),
                      IconButton(
                        icon: const Icon(Icons.menu),
                        onPressed: () {},
                      ),
                    ],
                  ),
                  const SizedBox(height: 16),

                  // Toggle online
                  OnlineToggle(
                    isOnline: isOnline,
                    isLoading: driverState.flowStatus == DriverFlowStatus.goingOnline,
                    onToggle: () => ref.read(driverProvider.notifier).toggleOnline(),
                  ),

                  if (isOnline) ...[
                    const SizedBox(height: 16),
                    // Ganancias
                    EarningsSummaryCard(
                      todayEarnings: driverState.todayEarnings,
                      todayTrips: driverState.todayTrips,
                      onTap: () => context.go('/driver/earnings'),
                    ),
                    const SizedBox(height: 12),
                    // Stats
                    DriverStatsRow(
                      totalTrips: profile?.totalTrips ?? 0,
                      rating: profile?.ratingDisplay ?? 0,
                      acceptanceRate: 85,
                    ),
                  ],
                ],
              ),
            ),
          ),

          // Panel de solicitudes
          if (driverState.pendingRequests.isNotEmpty)
            Positioned(
              left: 0,
              right: 0,
              bottom: 0,
              child: Container(
                height: MediaQuery.of(context).size.height * 0.4,
                decoration: const BoxDecoration(
                  color: Colors.white,
                  borderRadius: BorderRadius.vertical(top: Radius.circular(20)),
                ),
                child: Column(
                  children: [
                    Padding(
                      padding: const EdgeInsets.all(16),
                      child: Row(
                        mainAxisAlignment: MainAxisAlignment.spaceBetween,
                        children: [
                          Text(
                            'Solicitudes (${driverState.pendingRequestsCount})',
                            style: AppTextStyles.headingSmall,
                          ),
                          TextButton(
                            onPressed: () {},
                            child: const Text('Actualizar'),
                          ),
                        ],
                      ),
                    ),
                    Expanded(
                      child: ListView.builder(
                        padding: const EdgeInsets.symmetric(horizontal: 16),
                        itemCount: driverState.pendingRequests.length,
                        itemBuilder: (context, index) {
                          final request = driverState.pendingRequests[index];
                          return TripRequestCard(
                            request: request,
                            onMakeOffer: () => _showMakeOfferSheet(
                              context,
                              request,
                            ),
                            onReject: () {
                              ref.read(driverProvider.notifier).rejectRequest(
                                    request['trip_id'] as String,
                                  );
                            },
                          );
                        },
                      ),
                    ),
                  ],
                ),
              ),
            ),
        ],
      ),
    );
  }

  void _showMakeOfferSheet(
    BuildContext context,
    Map<String, dynamic> request,
  ) {
    final price = double.tryParse(request['proposed_price']?.toString() ?? '0') ?? 0;

    showModalBottomSheet(
      context: context,
      isScrollControlled: true,
      builder: (context) => MakeOfferSheet(
        tripRequest: request,
        suggestedPrice: price,
        onSubmit: (price, message) async {
          await ref.read(driverProvider.notifier).makeOffer(
                tripId: request['trip_id'] as String,
                price: price,
                message: message,
              );
          if (context.mounted) Navigator.pop(context);
        },
        onCancel: () => Navigator.pop(context),
      ),
    );
  }
}