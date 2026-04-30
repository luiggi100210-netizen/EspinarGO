import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import '../../../../core/theme/app_colors.dart';
import '../../../../core/theme/app_text_styles.dart';
import '../../../../shared/widgets/error_snackbar.dart';
import '../../domain/providers/trip_provider.dart';
import '../widgets/driver_offer_card.dart';

/// Pantalla donde el pasajero ve las ofertas de conductores.
class TripOffersScreen extends ConsumerWidget {
  const TripOffersScreen({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final tripState = ref.watch(tripProvider).valueOrNull;
    final offers = tripState?.offers ?? [];
    final proposedPrice = tripState?.currentTrip?.proposedPrice;

    return Scaffold(
      appBar: AppBar(
        title: Text('Ofertas (${offers.length})'),
        backgroundColor: Colors.transparent,
        elevation: 0,
      ),
      body: offers.isEmpty
          ? _buildEmptyState()
          : ListView.builder(
              padding: const EdgeInsets.all(16),
              itemCount: offers.length,
              itemBuilder: (context, index) {
                final offer = offers[index];
                return DriverOfferCard(
                  offer: offer,
                  proposedPrice: proposedPrice,
                  onAccept: () => _acceptOffer(context, ref, offer.id),
                );
              },
            ),
      bottomNavigationBar: Container(
        padding: const EdgeInsets.all(16),
        decoration: const BoxDecoration(
          color: Colors.white,
          boxShadow: [
            BoxShadow(
              color: Colors.black12,
              blurRadius: 10,
              offset: Offset(0, -2),
            ),
          ],
        ),
        child: SafeArea(
          child: ElevatedButton(
            onPressed: offers.isEmpty ? null : () {},
            style: ElevatedButton.styleFrom(
              backgroundColor: AppColors.primary,
              padding: const EdgeInsets.symmetric(vertical: 14),
            ),
            child: Text(
              offers.isEmpty
                  ? 'Selecciona una oferta'
                  : 'Selecciona una oferta (${offers.length} disponibles)',
            ),
          ),
        ),
      ),
    );
  }

  Widget _buildEmptyState() {
    return Center(
      child: Column(
        mainAxisAlignment: MainAxisAlignment.center,
        children: [
          const Text('🛺', style: TextStyle(fontSize: 64)),
          const SizedBox(height: 16),
          Text(
            'Los conductores están revisando tu solicitud...',
            style: AppTextStyles.bodyMedium.copyWith(
              color: AppColors.textSecondary,
            ),
            textAlign: TextAlign.center,
          ),
          const SizedBox(height: 8),
          const CircularProgressIndicator(),
        ],
      ),
    );
  }

  Future<void> _acceptOffer(BuildContext context, WidgetRef ref, String offerId) async {
    final success = await ref.read(tripProvider.notifier).acceptOffer(offerId);

    if (success && context.mounted) {
      context.go('/trip-active');
    } else if (context.mounted) {
      ErrorSnackbar.showError(context, 'Error al aceptar la oferta');
    }
  }
}