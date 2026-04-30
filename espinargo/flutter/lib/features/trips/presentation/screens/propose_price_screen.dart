import 'dart:convert';

import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import '../../../../core/theme/app_colors.dart';
import '../../../../core/theme/app_text_styles.dart';
import '../../../../shared/widgets/primary_button.dart';
import '../../../../shared/widgets/error_snackbar.dart';
import '../../../home/data/models/place_model.dart';
import '../../../home/data/models/route_model.dart';
import '../../domain/providers/trip_provider.dart';
import '../widgets/price_input_widget.dart';
import '../widgets/price_suggestions.dart';

/// Pantalla donde el pasajero propone el precio del viaje.
class ProposePriceScreen extends ConsumerStatefulWidget {
  final String routeJson;

  const ProposePriceScreen({
    super.key,
    required this.routeJson,
  });

  @override
  ConsumerState<ProposePriceScreen> createState() => _ProposePriceScreenState();
}

class _ProposePriceScreenState extends ConsumerState<ProposePriceScreen> {
  late RouteModel _route;
  String _selectedPrice = '';
  String _paymentMethod = 'cash';

  @override
  void initState() {
    super.initState();
    final data = jsonDecode(widget.routeJson) as Map<String, dynamic>;
    final origin = PlaceModel(
      placeId: data['origin_place_id'] as String? ?? '',
      name: data['origin_name'] as String? ?? '',
      address: data['origin_address'] as String? ?? '',
      lat: (data['origin_lat'] as num).toDouble(),
      lng: (data['origin_lng'] as num).toDouble(),
    );
    final destination = PlaceModel(
      placeId: data['dest_place_id'] as String? ?? '',
      name: data['dest_name'] as String? ?? '',
      address: data['dest_address'] as String? ?? '',
      lat: (data['dest_lat'] as num).toDouble(),
      lng: (data['dest_lng'] as num).toDouble(),
    );
    _route = RouteModel(
      origin: origin,
      destination: destination,
      distanceKm: (data['distance_km'] as num).toDouble(),
      durationMinutes: data['duration_minutes'] as int,
      polylinePoints: const [],
      suggestedPrice: (data['suggested_price'] as num).toDouble(),
      minPrice: (data['min_price'] as num).toDouble(),
      maxPrice: (data['max_price'] as num).toDouble(),
    );
    _selectedPrice = _route.suggestedPrice.toStringAsFixed(2);
  }

  Future<void> _createTrip() async {
    final price = double.tryParse(_selectedPrice) ?? 0;
    if (price <= 0) {
      ErrorSnackbar.showError(context, 'Ingresa un precio válido');
      return;
    }

    final success = await ref.read(tripProvider.notifier).createTrip(
      originAddress: _route.origin.address,
      originLat: _route.origin.lat,
      originLng: _route.origin.lng,
      destAddress: _route.destination.address,
      destLat: _route.destination.lat,
      destLng: _route.destination.lng,
      proposedPrice: _selectedPrice,
      paymentMethod: _paymentMethod,
    );

    if (success && mounted) {
      context.go('/waiting-drivers');
    } else if (mounted) {
      final state = ref.read(tripProvider).valueOrNull;
      ErrorSnackbar.showError(
        context,
        state?.errorMessage ?? 'Error al crear el viaje',
      );
    }
  }

  @override
  Widget build(BuildContext context) {
    final tripState = ref.watch(tripProvider);
    final isLoading = tripState.valueOrNull?.isLoading ?? false;

    return Scaffold(
      backgroundColor: AppColors.background,
      appBar: AppBar(
        title: const Text('Nuevo viaje'),
        backgroundColor: Colors.transparent,
        elevation: 0,
      ),
      body: SingleChildScrollView(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            // Info del viaje
            _buildRouteInfo(),
            const SizedBox(height: 24),

            // Título
            Text(
              '¿Cuánto quieres pagar?',
              style: AppTextStyles.headingLarge,
            ),
            const SizedBox(height: 4),
            Text(
              'Los conductores verán tu oferta',
              style: AppTextStyles.bodyMedium.copyWith(
                color: AppColors.textSecondary,
              ),
            ),
            const SizedBox(height: 24),

            // Precio input
            PriceInputWidget(
              initialPrice: _route.suggestedPrice,
              onPriceChanged: (price) {
                setState(() => _selectedPrice = price);
              },
            ),
            const SizedBox(height: 16),

            // Sugerencias
            PriceSuggestions(
              suggestedPrice: _route.suggestedPrice,
              selectedPrice: double.tryParse(_selectedPrice),
              onPriceSelected: (price) {
                setState(() => _selectedPrice = price.toStringAsFixed(2));
              },
            ),
            const SizedBox(height: 24),

            // Método de pago
            Text('Método de pago', style: AppTextStyles.labelLarge),
            const SizedBox(height: 12),
            Row(
              children: [
                _buildPaymentOption('cash', '💵', 'Efectivo'),
                const SizedBox(width: 12),
                _buildPaymentOption('yape', '📱', 'Yape'),
                const SizedBox(width: 12),
                _buildPaymentOption('plin', '📱', 'Plin'),
              ],
            ),
            const SizedBox(height: 32),

            // Botón
            PrimaryButton(
              text: 'Buscar conductores',
              onPressed: _createTrip,
              isLoading: isLoading,
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildRouteInfo() {
    return Container(
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        color: Colors.white,
        borderRadius: BorderRadius.circular(12),
      ),
      child: Row(
        children: [
          Column(
            children: [
              Container(
                width: 10,
                height: 10,
                decoration: const BoxDecoration(
                  color: AppColors.success,
                  shape: BoxShape.circle,
                ),
              ),
              Container(
                width: 2,
                height: 30,
                color: AppColors.border,
              ),
              Container(
                width: 10,
                height: 10,
                decoration: const BoxDecoration(
                  color: AppColors.primary,
                  shape: BoxShape.circle,
                ),
              ),
            ],
          ),
          const SizedBox(width: 12),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  _route.origin.shortAddress,
                  style: AppTextStyles.bodyMedium,
                  maxLines: 1,
                  overflow: TextOverflow.ellipsis,
                ),
                const SizedBox(height: 24),
                Text(
                  _route.destination.shortAddress,
                  style: AppTextStyles.bodyMedium,
                  maxLines: 1,
                  overflow: TextOverflow.ellipsis,
                ),
              ],
            ),
          ),
          Column(
            crossAxisAlignment: CrossAxisAlignment.end,
            children: [
              Text(_route.formattedDistance, style: AppTextStyles.labelMedium),
              Text(_route.formattedDuration, style: AppTextStyles.bodySmall),
            ],
          ),
        ],
      ),
    );
  }

  Widget _buildPaymentOption(String value, String emoji, String label) {
    final isSelected = _paymentMethod == value;

    return Expanded(
      child: GestureDetector(
        onTap: () => setState(() => _paymentMethod = value),
        child: Container(
          padding: const EdgeInsets.symmetric(vertical: 12),
          decoration: BoxDecoration(
            color: isSelected ? AppColors.primaryLight : Colors.white,
            borderRadius: BorderRadius.circular(12),
            border: Border.all(
              color: isSelected ? AppColors.primary : AppColors.border,
              width: isSelected ? 2 : 1,
            ),
          ),
          child: Column(
            children: [
              Text(emoji, style: const TextStyle(fontSize: 24)),
              const SizedBox(height: 4),
              Text(
                label,
                style: AppTextStyles.labelSmall.copyWith(
                  color: isSelected ? AppColors.primary : AppColors.textSecondary,
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }
}