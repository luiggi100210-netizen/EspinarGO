import 'package:flutter/material.dart';

import '../../../../core/theme/app_colors.dart';
import '../../../../core/theme/app_text_styles.dart';
import '../../../../shared/widgets/primary_button.dart';
import '../widgets/make_offer_sheet.dart';

/// Pantalla de detalle de una solicitud de viaje.
class TripRequestScreen extends StatelessWidget {
  final Map<String, dynamic> tripRequest;

  const TripRequestScreen({
    super.key,
    required this.tripRequest,
  });

  @override
  Widget build(BuildContext context) {
    final price = double.tryParse(tripRequest['proposed_price']?.toString() ?? '0') ?? 0;

    return Scaffold(
      backgroundColor: AppColors.background,
      appBar: AppBar(
        title: const Text('Solicitud de viaje'),
        backgroundColor: Colors.transparent,
        elevation: 0,
      ),
      body: SingleChildScrollView(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            // Info del viaje (simulado)
            Container(
              padding: const EdgeInsets.all(16),
              decoration: BoxDecoration(
                color: Colors.white,
                borderRadius: BorderRadius.circular(16),
              ),
              child: Column(
                children: [
                  Row(
                    children: [
                      Container(
                        width: 12,
                        height: 12,
                        decoration: const BoxDecoration(
                          color: AppColors.success,
                          shape: BoxShape.circle,
                        ),
                      ),
                      const SizedBox(width: 12),
                      Expanded(
                        child: Text(
                          tripRequest['origin_address'] ?? 'Origen',
                          style: AppTextStyles.bodyMedium,
                        ),
                      ),
                    ],
                  ),
                  const SizedBox(height: 24),
                  Row(
                    children: [
                      Container(
                        width: 12,
                        height: 12,
                        decoration: const BoxDecoration(
                          color: AppColors.primary,
                          shape: BoxShape.circle,
                        ),
                      ),
                      const SizedBox(width: 12),
                      Expanded(
                        child: Text(
                          tripRequest['dest_address'] ?? 'Destino',
                          style: AppTextStyles.bodyMedium,
                        ),
                      ),
                    ],
                  ),
                ],
              ),
            ),
            const SizedBox(height: 24),

            // Precio
            Center(
              child: Column(
                children: [
                  Text('Precio propuesto', style: AppTextStyles.labelMedium),
                  Text(
                    'S/ ${price.toStringAsFixed(2)}',
                    style: AppTextStyles.priceDisplay,
                  ),
                ],
              ),
            ),
            const SizedBox(height: 32),

            // Botón oferta
            PrimaryButton(
              text: 'Hacer oferta',
              onPressed: () {
                showModalBottomSheet(
                  context: context,
                  isScrollControlled: true,
                  builder: (context) => MakeOfferSheet(
                    tripRequest: tripRequest,
                    suggestedPrice: price,
                    onSubmit: (p, m) {
                      Navigator.pop(context);
                    },
                    onCancel: () => Navigator.pop(context),
                  ),
                );
              },
            ),
            const SizedBox(height: 12),

            // Ignorar
            Center(
              child: TextButton(
                onPressed: () => Navigator.pop(context),
                child: Text(
                  'Ignorar esta solicitud',
                  style: AppTextStyles.labelMedium.copyWith(
                    color: AppColors.textSecondary,
                  ),
                ),
              ),
            ),
          ],
        ),
      ),
    );
  }
}