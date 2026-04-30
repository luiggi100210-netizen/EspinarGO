import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import '../../../../core/theme/app_colors.dart';
import '../../../../core/theme/app_text_styles.dart';
import '../../../../core/utils/validators.dart';
import '../../../../shared/widgets/error_snackbar.dart';
import '../../../../shared/widgets/primary_button.dart';
import '../../domain/providers/auth_provider.dart';
import '../widgets/auth_text_field.dart';

/// Pantalla para establecer una nueva contraseña con el OTP verificado.
class ResetPasswordScreen extends ConsumerStatefulWidget {
  final String phone;

  const ResetPasswordScreen({super.key, required this.phone});

  @override
  ConsumerState<ResetPasswordScreen> createState() =>
      _ResetPasswordScreenState();
}

class _ResetPasswordScreenState extends ConsumerState<ResetPasswordScreen> {
  final _formKey = GlobalKey<FormState>();
  final _otpController = TextEditingController();
  final _passwordController = TextEditingController();
  final _confirmController = TextEditingController();
  bool _obscurePassword = true;
  bool _obscureConfirm = true;

  @override
  void dispose() {
    _otpController.dispose();
    _passwordController.dispose();
    _confirmController.dispose();
    super.dispose();
  }

  Future<void> _reset() async {
    if (!_formKey.currentState!.validate()) return;

    final success = await ref.read(authProvider.notifier).resetPassword(
          widget.phone,
          _otpController.text.trim(),
          _passwordController.text,
        );

    if (!mounted) return;

    if (success) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(
          content: Text('Contraseña actualizada correctamente'),
          backgroundColor: AppColors.success,
        ),
      );
      context.go('/login');
    } else {
      final error =
          ref.read(authProvider).error?.toString() ?? 'Error al restablecer';
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
        child: SingleChildScrollView(
          padding: const EdgeInsets.all(24),
          child: Form(
            key: _formKey,
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.stretch,
              children: [
                const SizedBox(height: 16),
                Text('Nueva contraseña', style: AppTextStyles.displayMedium),
                const SizedBox(height: 8),
                Text(
                  'Ingresa el código que recibiste y tu nueva contraseña.',
                  style: AppTextStyles.bodyMedium.copyWith(
                    color: AppColors.textSecondary,
                  ),
                ),
                const SizedBox(height: 32),
                AuthTextField(
                  controller: _otpController,
                  label: 'Código de verificación',
                  hint: '000000',
                  prefixIcon: Icons.verified_outlined,
                  keyboardType: TextInputType.number,
                  maxLength: 6,
                  validator: Validators.otpCode,
                ),
                const SizedBox(height: 16),
                AuthTextField(
                  controller: _passwordController,
                  label: 'Nueva contraseña',
                  hint: 'Mínimo 6 caracteres',
                  prefixIcon: Icons.lock_outline,
                  obscureText: _obscurePassword,
                  suffixIcon: _obscurePassword
                      ? Icons.visibility_off_outlined
                      : Icons.visibility_outlined,
                  onSuffixIconTap: () =>
                      setState(() => _obscurePassword = !_obscurePassword),
                  validator: Validators.password,
                ),
                const SizedBox(height: 16),
                AuthTextField(
                  controller: _confirmController,
                  label: 'Confirmar contraseña',
                  hint: 'Repite tu nueva contraseña',
                  prefixIcon: Icons.lock_outline,
                  obscureText: _obscureConfirm,
                  suffixIcon: _obscureConfirm
                      ? Icons.visibility_off_outlined
                      : Icons.visibility_outlined,
                  onSuffixIconTap: () =>
                      setState(() => _obscureConfirm = !_obscureConfirm),
                  validator: (value) {
                    if (value != _passwordController.text) {
                      return 'Las contraseñas no coinciden';
                    }
                    return null;
                  },
                  textInputAction: TextInputAction.done,
                  onSubmitted: (_) => _reset(),
                ),
                const SizedBox(height: 32),
                PrimaryButton(
                  text: 'Guardar contraseña',
                  onPressed: _reset,
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
