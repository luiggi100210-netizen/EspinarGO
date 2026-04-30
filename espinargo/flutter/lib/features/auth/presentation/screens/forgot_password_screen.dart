import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import '../../../../core/theme/app_colors.dart';
import '../../../../core/theme/app_text_styles.dart';
import '../../../../core/utils/validators.dart';
import '../../../../shared/widgets/error_snackbar.dart';
import '../../../../shared/widgets/primary_button.dart';
import '../../domain/providers/auth_provider.dart';
import '../widgets/phone_field.dart';

/// Pantalla para solicitar recuperación de contraseña.
class ForgotPasswordScreen extends ConsumerStatefulWidget {
  const ForgotPasswordScreen({super.key});

  @override
  ConsumerState<ForgotPasswordScreen> createState() =>
      _ForgotPasswordScreenState();
}

class _ForgotPasswordScreenState extends ConsumerState<ForgotPasswordScreen> {
  final _formKey = GlobalKey<FormState>();
  final _phoneController = TextEditingController();

  @override
  void dispose() {
    _phoneController.dispose();
    super.dispose();
  }

  Future<void> _sendCode() async {
    if (!_formKey.currentState!.validate()) return;

    final phone = PhoneField.buildFullPhone(_phoneController.text.trim());
    final success = await ref.read(authProvider.notifier).forgotPassword(phone);

    if (!mounted) return;

    if (success) {
      context.push(
        Uri(
          path: '/otp',
          queryParameters: {
            'phone': phone,
            'purpose': 'forgot_password',
          },
        ).toString(),
      );
    } else {
      final error =
          ref.read(authProvider).error?.toString() ?? 'Error al enviar el código';
      ErrorSnackbar.showError(context, error);
    }
  }

  @override
  Widget build(BuildContext context) {
    final isLoading = ref.watch(authProvider).isLoading;

    return Scaffold(
      backgroundColor: AppColors.background,
      appBar: AppBar(
        backgroundColor: Colors.transparent,
        elevation: 0,
        leading: IconButton(
          icon: const Icon(Icons.arrow_back_ios, color: AppColors.textPrimary),
          onPressed: () => context.pop(),
        ),
      ),
      body: SafeArea(
        child: Padding(
          padding: const EdgeInsets.all(24),
          child: Form(
            key: _formKey,
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.stretch,
              children: [
                const SizedBox(height: 16),
                const Text('🔑', style: TextStyle(fontSize: 48)),
                const SizedBox(height: 16),
                Text('¿Olvidaste tu contraseña?', style: AppTextStyles.displayMedium),
                const SizedBox(height: 8),
                Text(
                  'Ingresa tu número y te enviaremos un código para restablecer tu contraseña.',
                  style: AppTextStyles.bodyMedium.copyWith(
                    color: AppColors.textSecondary,
                  ),
                ),
                const SizedBox(height: 32),
                PhoneField(
                  controller: _phoneController,
                  validator: Validators.phone,
                ),
                const SizedBox(height: 32),
                PrimaryButton(
                  text: 'Enviar código',
                  onPressed: _sendCode,
                  isLoading: isLoading,
                ),
              ],
            ),
          ),
        ),
      ),
    );
  }
}
