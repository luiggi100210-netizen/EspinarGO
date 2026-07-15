import 'package:flutter/material.dart';
import 'package:flutter/services.dart';

import '../../../../core/theme/app_colors.dart';
import '../../../../core/theme/app_text_styles.dart';

/// Widget para que el pasajero escriba el precio.
/// Diseño premium con teclado numérico grande.
class PriceInputWidget extends StatefulWidget {
  final double initialPrice;
  final ValueChanged<String> onPriceChanged;
  final double minPrice;
  final double maxPrice;

  const PriceInputWidget({
    super.key,
    required this.initialPrice,
    required this.onPriceChanged,
    this.minPrice = 3.0,
    this.maxPrice = 50.0,
  });

  @override
  State<PriceInputWidget> createState() => _PriceInputWidgetState();
}

class _PriceInputWidgetState extends State<PriceInputWidget> {
  late TextEditingController _controller;
  String _priceText = '';

  @override
  void initState() {
    super.initState();
    _priceText = widget.initialPrice.toStringAsFixed(2);
    _controller = TextEditingController(text: _priceText);
  }

  @override
  void dispose() {
    _controller.dispose();
    super.dispose();
  }

  void _onTextChanged(String value) {
    // Solo permitir números y un punto
    final filtered = value.replaceAll(RegExp(r'[^0-9.]'), '');
    
    // Solo un punto
    final parts = filtered.split('.');
    String result = parts[0];
    if (parts.length > 1) {
      result += '.${parts[1].substring(0, parts[1].length.clamp(0, 2))}';
    }

    setState(() {
      _priceText = result;
    });

    widget.onPriceChanged(result);
  }

  String _getPriceStatus() {
    final price = double.tryParse(_priceText) ?? 0;
    if (price < widget.minPrice) return 'Muy bajo, pocos conductores';
    if (price > widget.maxPrice) return 'Precio alto';
    return 'Buen precio';
  }

  Color _getStatusColor() {
    final price = double.tryParse(_priceText) ?? 0;
    if (price < widget.minPrice) return AppColors.error;
    if (price > widget.maxPrice) return AppColors.warning;
    return AppColors.success;
  }

  @override
  Widget build(BuildContext context) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Row(
          crossAxisAlignment: CrossAxisAlignment.center,
          children: [
            Text(
              'S/',
              style: AppTextStyles.displayMedium.copyWith(
                color: AppColors.primary,
              ),
            ),
            const SizedBox(width: 8),
            Expanded(
              child: TextField(
                controller: _controller,
                keyboardType: const TextInputType.numberWithOptions(decimal: true),
                onChanged: _onTextChanged,
                style: AppTextStyles.displayLarge.copyWith(
                  fontSize: 48,
                  fontWeight: FontWeight.bold,
                ),
                decoration: const InputDecoration(
                  border: InputBorder.none,
                  contentPadding: EdgeInsets.zero,
                ),
              ),
            ),
          ],
        ),
        const SizedBox(height: 8),
        Text(
          'Precio sugerido: S/ ${widget.initialPrice.toStringAsFixed(2)}',
          style: AppTextStyles.bodySmall,
        ),
        const SizedBox(height: 12),
        // Barra de rango
        _buildRangeBar(),
        const SizedBox(height: 8),
        Text(
          _getPriceStatus(),
          style: AppTextStyles.labelSmall.copyWith(
            color: _getStatusColor(),
          ),
        ),
      ],
    );
  }

  Widget _buildRangeBar() {
    final price = double.tryParse(_priceText) ?? 0;
    final isValid = price >= widget.minPrice && price <= widget.maxPrice;
    final progress = ((price - widget.minPrice) / (widget.maxPrice - widget.minPrice))
        .clamp(0.0, 1.0);

    return Container(
      height: 8,
      decoration: BoxDecoration(
        color: AppColors.border,
        borderRadius: BorderRadius.circular(4),
      ),
      child: FractionallySizedBox(
        alignment: Alignment.centerLeft,
        widthFactor: progress,
        child: Container(
          decoration: BoxDecoration(
            color: isValid ? AppColors.success : AppColors.warning,
            borderRadius: BorderRadius.circular(4),
          ),
        ),
      ),
    );
  }
}