import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import '../../../../core/theme/app_colors.dart';
import '../../../../core/theme/app_text_styles.dart';
import '../../../../core/utils/validators.dart';
import '../../../../shared/widgets/espinargo_logo.dart';
import '../../../../shared/widgets/error_snackbar.dart';
import '../../../../shared/widgets/primary_button.dart';
import '../../domain/providers/auth_provider.dart';
import '../widgets/auth_text_field.dart';
import '../widgets/phone_field.dart';

/// Pantalla de inicio de sesión.
class LoginScreen extends ConsumerStatefulWidget {
  const LoginScreen({super.key});

  @override
  ConsumerState<LoginScreen> createState() => _LoginScreenState();
}

class _LoginScreenState extends ConsumerState<LoginScreen> {
  final _formKey = GlobalKey<FormState>();
  final _phoneController = TextEditingController();
  final _passwordController = TextEditingController();
  bool _obscurePassword = true;

  @override
  void dispose() {
    _phoneController.dispose();
    _passwordController.dispose();
    super.dispose();
  }

  Future<void> _login() async {
    if (!_formKey.currentState!.validate()) return;

    final phone = PhoneField.buildFullPhone(_phoneController.text.trim());
    final success = await ref.read(authProvider.notifier).login(
          phone,
          _passwordController.text,
        );

    if (!mounted) return;

    if (success) {
      final authState = ref.read(authProvider).valueOrNull;
      context.go(authState?.isDriver == true ? '/driver/dashboard' : '/home');
    } else {
      final error = ref.read(authProvider).error?.toString() ??
          'Error al iniciar sesión';
      ErrorSnackbar.showError(context, error);
    }
  }

  @override
  Widget build(BuildContext context) {
    final isLoading = ref.watch(authProvider).isLoading;

    return Scaffold(
      backgroundColor: AppColors.background,
      body: SafeArea(
        child: SingleChildScrollView(
          padding: const EdgeInsets.all(24),
          child: Form(
            key: _formKey,
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.stretch,
              children: [
                const SizedBox(height: 32),
                Center(
                  child: EspinarGoLogo(
                    size: 'medium',
                    color: AppColors.primary,
                  ),
                ),
                const SizedBox(height: 40),
                Text('Bienvenido', style: AppTextStyles.displayMedium),
                const SizedBox(height: 4),
                Text(
                  'Ingresa tu número y contraseña',
                  style: AppTextStyles.bodyMedium.copyWith(
                    color: AppColors.textSecondary,
                  ),
                ),
                const SizedBox(height: 32),
                PhoneField(
                  controller: _phoneController,
                  validator: Validators.phone,
                ),
                const SizedBox(height: 16),
                AuthTextField(
                  controller: _passwordController,
                  label: 'Contraseña',
                  hint: '••••••••',
                  prefixIcon: Icons.lock_outline,
                  obscureText: _obscurePassword,
                  suffixIcon: _obscurePassword
                      ? Icons.visibility_off_outlined
                      : Icons.visibility_outlined,
                  onSuffixIconTap: () =>
                      setState(() => _obscurePassword = !_obscurePassword),
                  validator: Validators.password,
                  textInputAction: TextInputAction.done,
                  onSubmitted: (_) => _login(),
                ),
                const SizedBox(height: 12),
                Align(
                  alignment: Alignment.centerRight,
                  child: TextButton(
                    onPressed: () => context.push('/forgot-password'),
                    child: Text(
                      '¿Olvidaste tu contraseña?',
                      style: AppTextStyles.labelMedium.copyWith(
                        color: AppColors.primary,
                      ),
                    ),
                  ),
                ),
                const SizedBox(height: 24),
                PrimaryButton(
                  text: 'Iniciar sesión',
                  onPressed: _login,
                  isLoading: isLoading,
                ),
                const SizedBox(height: 32),
                Row(
                  mainAxisAlignment: MainAxisAlignment.center,
                  children: [
                    Text('¿No tienes cuenta? ', style: AppTextStyles.bodyMedium),
                    GestureDetector(
                      onTap: () => context.go('/role-selection'),
                      child: Text(
                        'Regístrate',
                        style: AppTextStyles.bodyMedium.copyWith(
                          color: AppColors.primary,
                          fontWeight: FontWeight.w600,
                        ),
                      ),
                    ),
                  ],
                ),
              ],
            ),
          ),
        ),
      ),
    );
  }
}
