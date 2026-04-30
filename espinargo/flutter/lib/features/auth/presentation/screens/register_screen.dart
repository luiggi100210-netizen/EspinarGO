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
import '../widgets/phone_field.dart';

/// Pantalla de registro de nuevo usuario.
class RegisterScreen extends ConsumerStatefulWidget {
  final String role;

  const RegisterScreen({super.key, required this.role});

  @override
  ConsumerState<RegisterScreen> createState() => _RegisterScreenState();
}

class _RegisterScreenState extends ConsumerState<RegisterScreen> {
  final _formKey = GlobalKey<FormState>();
  final _nameController = TextEditingController();
  final _phoneController = TextEditingController();
  final _passwordController = TextEditingController();
  final _confirmController = TextEditingController();
  bool _obscurePassword = true;
  bool _obscureConfirm = true;

  @override
  void dispose() {
    _nameController.dispose();
    _phoneController.dispose();
    _passwordController.dispose();
    _confirmController.dispose();
    super.dispose();
  }

  String get _roleLabel => widget.role == 'driver' ? 'Conductor' : 'Pasajero';

  Future<void> _register() async {
    if (!_formKey.currentState!.validate()) return;

    final phone = PhoneField.buildFullPhone(_phoneController.text.trim());

    final success = await ref.read(authProvider.notifier).register(
          fullName: _nameController.text.trim(),
          phoneNumber: phone,
          password: _passwordController.text,
          role: widget.role,
        );

    if (!mounted) return;

    if (success) {
      context.push(
        Uri(
          path: '/otp',
          queryParameters: {
            'phone': phone,
            'purpose': 'phone_verify',
          },
        ).toString(),
      );
    } else {
      final error = ref.read(authProvider).error?.toString() ?? 'Error al registrar';
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
        title: Text('Crear cuenta · $_roleLabel', style: AppTextStyles.headingSmall),
      ),
      body: SafeArea(
        child: SingleChildScrollView(
          padding: const EdgeInsets.all(24),
          child: Form(
            key: _formKey,
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.stretch,
              children: [
                AuthTextField(
                  controller: _nameController,
                  label: 'Nombre completo',
                  hint: 'Juan Quispe',
                  prefixIcon: Icons.person_outline,
                  validator: Validators.name,
                ),
                const SizedBox(height: 16),
                PhoneField(
                  controller: _phoneController,
                  validator: Validators.phone,
                ),
                const SizedBox(height: 16),
                AuthTextField(
                  controller: _passwordController,
                  label: 'Contraseña',
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
                  hint: 'Repite tu contraseña',
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
                  onSubmitted: (_) => _register(),
                ),
                const SizedBox(height: 32),
                PrimaryButton(
                  text: 'Crear cuenta',
                  onPressed: _register,
                  isLoading: isLoading,
                ),
                const SizedBox(height: 16),
                Text(
                  'Al registrarte aceptas los términos de servicio de EspinarGo',
                  style: AppTextStyles.bodySmall,
                  textAlign: TextAlign.center,
                ),
              ],
            ),
          ),
        ),
      ),
    );
  }
}
