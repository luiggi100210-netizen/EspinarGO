import 'package:flutter/material.dart';

import '../../../../core/theme/app_colors.dart';
import '../../../../core/theme/app_text_styles.dart';

/// Sheet para hacer oferta de precio.
class MakeOfferSheet extends StatefulWidget {
  final Map<String, dynamic> tripRequest;
  final double suggestedPrice;
  final Function(String price, String? message) onSubmit;
  final VoidCallback onCancel;

  const MakeOfferSheet({
    super.key,
    required this.tripRequest,
    required this.suggestedPrice,
    required this.onSubmit,
    required this.onCancel,
  });

  @override
  State<MakeOfferSheet> createState() => _MakeOfferSheetState();
}

class _MakeOfferSheetState extends State<MakeOfferSheet> {
  late TextEditingController _priceController;
  final TextEditingController _messageController = TextEditingController();

  @override
  void initState() {
    super.initState();
    _priceController = TextEditingController(
      text: widget.suggestedPrice.toStringAsFixed(2),
    );
  }

  @override
  void dispose() {
    _priceController.dispose();
    _messageController.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final price = double.tryParse(_priceController.text) ?? 0;
    final isPriceHigh = price > widget.suggestedPrice * 1.5;

    return Container(
      padding: const EdgeInsets.all(24),
      decoration: const BoxDecoration(
        color: Colors.white,
        borderRadius: BorderRadius.vertical(top: Radius.circular(20)),
      ),
      child: Column(
        mainAxisSize: MainAxisSize.min,
        children: [
          // Header
          Text(
            'Tu oferta al pasajero',
            style: AppTextStyles.headingMedium,
          ),
          Text(
            'Precio del pasajero: ${widget.suggestedPrice.toStringAsFixed(2)}',
            style: AppTextStyles.bodySmall,
          ),
          const SizedBox(height: 24),

          // Precio input
          Row(
            children: [
              Text('S/', style: AppTextStyles.priceDisplay),
              const SizedBox(width: 8),
              Expanded(
                child: TextField(
                  controller: _priceController,
                  keyboardType: const TextInputType.numberWithOptions(decimal: true),
                  style: AppTextStyles.priceDisplay,
                  decoration: const InputDecoration(
                    border: InputBorder.none,
                    contentPadding: EdgeInsets.zero,
                  ),
                ),
              ),
            ],
          ),
          if (isPriceHigh)
            Container(
              padding: const EdgeInsets.all(8),
              decoration: BoxDecoration(
                color: AppColors.warningLight,
                borderRadius: BorderRadius.circular(8),
              ),
              child: Text(
                'Tu precio es muy alto, es poco probable que te elijan',
                style: AppTextStyles.bodySmall.copyWith(color: AppColors.warning),
              ),
            ),
          const SizedBox(height: 16),

          // Opciones rápidas
          Row(
            children: [
              _buildPriceChip(price - 1),
              _buildPriceChip(price),
              _buildPriceChip(price + 1),
            ],
          ),
          const SizedBox(height: 16),

          // Mensaje opcional
          TextField(
            controller: _messageController,
            maxLength: 100,
            maxLines: 2,
            decoration: InputDecoration(
              hintText: 'Mensaje opcional (ej: Llego en 3 min)',
              border: OutlineInputBorder(
                borderRadius: BorderRadius.circular(12),
              ),
            ),
          ),
          const SizedBox(height: 24),

          // Botones
          Row(
            children: [
              Expanded(
                child: TextButton(
                  onPressed: widget.onCancel,
                  child: const Text('Cancelar'),
                ),
              ),
              const SizedBox(width: 12),
              Expanded(
                child: ElevatedButton(
                  onPressed: () {
                    widget.onSubmit(
                      _priceController.text,
                      _messageController.text.isNotEmpty
                          ? _messageController.text
                          : null,
                    );
                  },
                  child: const Text('Enviar oferta'),
                ),
              ),
            ],
          ),
        ],
      ),
    );
  }

  Widget _buildPriceChip(double price) {
    if (price <= 0) return const SizedBox();
    return Expanded(
      child: GestureDetector(
        onTap: () {
          setState(() {
            _priceController.text = price.toStringAsFixed(2);
          });
        },
        child: Container(
          margin: const EdgeInsets.symmetric(horizontal: 4),
          padding: const EdgeInsets.symmetric(vertical: 8),
          decoration: BoxDecoration(
            border: Border.all(color: AppColors.border),
            borderRadius: BorderRadius.circular(8),
          ),
          child: Center(
            child: Text(
              'S/ ${price.toStringAsFixed(0)}',
              style: AppTextStyles.labelMedium,
            ),
          ),
        ),
      ),
    );
  }
}