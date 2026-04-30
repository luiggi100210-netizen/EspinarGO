import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import '../../../../core/theme/app_colors.dart';
import '../../../../core/theme/app_text_styles.dart';
import '../../../../shared/widgets/primary_button.dart';
import '../../../../shared/widgets/error_snackbar.dart';
import '../../../auth/presentation/widgets/phone_field.dart';
import '../../../auth/presentation/widgets/auth_text_field.dart';
import '../../domain/providers/package_provider.dart';
import '../widgets/package_size_selector.dart';

/// Pantalla para crear una nueva encomienda.
class SendPackageScreen extends ConsumerStatefulWidget {
  const SendPackageScreen({super.key});

  @override
  ConsumerState<SendPackageScreen> createState() => _SendPackageScreenState();
}

class _SendPackageScreenState extends ConsumerState<SendPackageScreen> {
  final _formKey = GlobalKey<FormState>();
  final _nameController = TextEditingController();
  final _phoneController = TextEditingController();
  final _addressController = TextEditingController();
  final _descriptionController = TextEditingController();

  String _size = 'small';
  bool _isFragile = false;
  String _paymentMethod = 'cash';
  int _step = 1;

  @override
  void dispose() {
    _nameController.dispose();
    _phoneController.dispose();
    _addressController.dispose();
    _descriptionController.dispose();
    super.dispose();
  }

  String _getEstimatedPrice() {
    switch (_size) {
      case 'envelope':
        return 'S/ 3.00 - S/ 5.00';
      case 'small':
        return 'S/ 5.00 - S/ 8.00';
      case 'medium':
        return 'S/ 8.00 - S/ 15.00';
      case 'large':
        return 'S/ 15.00 - S/ 30.00';
      default:
        return 'S/ 5.00 - S/ 15.00';
    }
  }

  Future<void> _createPackage() async {
    if (!_formKey.currentState!.validate()) return;

    final success = await ref.read(packageProvider.notifier).createPackage(
          recipientName: _nameController.text,
          recipientPhone: PhoneField.buildFullPhone(_phoneController.text),
          deliveryAddress: _addressController.text,
          size: _size,
          description: _descriptionController.text,
          isFragile: _isFragile,
          paymentMethod: _paymentMethod,
        );

    if (success && mounted) {
      final package = ref.read(packageProvider).valueOrNull?.lastCreatedPackage;
      context.go('/packages/track?code=${package?.trackingCode}');
    } else if (mounted) {
      ErrorSnackbar.showError(context, 'Error al crear la encomienda');
    }
  }

  @override
  Widget build(BuildContext context) {
    final packageState = ref.watch(packageProvider);
    final isLoading = packageState.valueOrNull?.isCreating ?? false;

    return Scaffold(
      appBar: AppBar(
        title: Text(_step == 1 ? 'Datos del destinatario' : 'Datos del paquete'),
        backgroundColor: Colors.transparent,
      ),
      body: SingleChildScrollView(
        padding: const EdgeInsets.all(16),
        child: Form(
          key: _formKey,
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              // Progress
              LinearProgressIndicator(value: _step / 2, backgroundColor: AppColors.border),
              const SizedBox(height: 24),

              if (_step == 1) ...[
                AuthTextField(
                  controller: _nameController,
                  label: 'Nombre del destinatario',
                  hint: 'Juan Quispe',
                  prefixIcon: Icons.person,
                  validator: (v) => v?.isEmpty == true ? 'Ingresa el nombre' : null,
                ),
                const SizedBox(height: 16),
                PhoneField(controller: _phoneController),
                const SizedBox(height: 16),
                AuthTextField(
                  controller: _addressController,
                  label: 'Dirección de entrega',
                  hint: 'Av. Principal 123, Espinar',
                  prefixIcon: Icons.location_on,
                  maxLines: 2,
                  validator: (v) => v?.isEmpty == true ? 'Ingresa la dirección' : null,
                ),
                const SizedBox(height: 32),
                PrimaryButton(
                  text: 'Continuar →',
                  onPressed: () {
                    if (_formKey.currentState!.validate()) {
                      setState(() => _step = 2);
                    }
                  },
                ),
              ] else ...[
                Text('Tamaño del paquete', style: AppTextStyles.labelLarge),
                const SizedBox(height: 12),
                PackageSizeSelector(
                  selectedSize: _size,
                  onSizeSelected: (s) => setState(() => _size = s),
                ),
                const SizedBox(height: 24),
                AuthTextField(
                  controller: _descriptionController,
                  label: '¿Qué contiene el paquete?',
                  hint: 'Ropa, documentos, medicamentos...',
                  prefixIcon: Icons.inventory_2,
                  maxLines: 3,
                  validator: (v) => v?.isEmpty == true ? 'Describe el contenido' : null,
                ),
                const SizedBox(height: 16),
                Row(
                  children: [
                    Text('¿Es frágil?', style: AppTextStyles.bodyMedium),
                    const Spacer(),
                    Switch(
                      value: _isFragile,
                      onChanged: (v) => setState(() => _isFragile = v),
                      activeColor: AppColors.package,
                    ),
                  ],
                ),
                const SizedBox(height: 24),
                Text('Método de pago', style: AppTextStyles.labelLarge),
                const SizedBox(height: 12),
                Row(
                  children: [
                    _buildPaymentChip('cash', '💵', 'Efectivo'),
                    _buildPaymentChip('yape', '📱', 'Yape'),
                    _buildPaymentChip('plin', '📱', 'Plin'),
                  ],
                ),
                const SizedBox(height: 16),
                Container(
                  padding: const EdgeInsets.all(12),
                  decoration: BoxDecoration(
                    color: AppColors.infoLight,
                    borderRadius: BorderRadius.circular(8),
                  ),
                  child: Text('Precio estimado: ${_getEstimatedPrice()}', style: AppTextStyles.bodyMedium),
                ),
                const SizedBox(height: 32),
                PrimaryButton(
                  text: 'Enviar encomienda',
                  isLoading: isLoading,
                  onPressed: _createPackage,
                ),
                const SizedBox(height: 12),
                Center(
                  child: TextButton(
                    onPressed: () => setState(() => _step = 1),
                    child: const Text('Volver'),
                  ),
                ),
              ],
            ],
          ),
        ),
      ),
    );
  }

  Widget _buildPaymentChip(String value, String emoji, String label) {
    final isSelected = _paymentMethod == value;
    return Expanded(
      child: GestureDetector(
        onTap: () => setState(() => _paymentMethod = value),
        child: Container(
          margin: const EdgeInsets.only(right: 8),
          padding: const EdgeInsets.symmetric(vertical: 12),
          decoration: BoxDecoration(
            color: isSelected ? AppColors.packageLight : Colors.white,
            borderRadius: BorderRadius.circular(12),
            border: Border.all(color: isSelected ? AppColors.package : AppColors.border),
          ),
          child: Column(
            children: [
              Text(emoji),
              const SizedBox(height: 4),
              Text(label, style: AppTextStyles.labelSmall),
            ],
          ),
        ),
      ),
    );
  }
}