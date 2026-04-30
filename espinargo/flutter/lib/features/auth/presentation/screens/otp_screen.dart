import 'dart:async';

import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import 'package:pinput/pinput.dart';

import '../../../../core/constants/app_constants.dart';
import '../../../../core/theme/app_colors.dart';
import '../../../../core/theme/app_text_styles.dart';
import '../../../../shared/widgets/error_snackbar.dart';
import '../../../../shared/widgets/primary_button.dart';
import '../../domain/providers/auth_provider.dart';

/// Pantalla de verificación OTP (6 dígitos).
class OTPScreen extends ConsumerStatefulWidget {
  final String phone;
  final String purpose;

  const OTPScreen({super.key, required this.phone, required this.purpose});

  @override
  ConsumerState<OTPScreen> createState() => _OTPScreenState();
}

class _OTPScreenState extends ConsumerState<OTPScreen> {
  final _otpController = TextEditingController();
  int _secondsLeft = AppConstants.OTP_RESEND_SECONDS;
  Timer? _timer;
  bool _canResend = false;

  @override
  void initState() {
    super.initState();
    _startTimer();
  }

  @override
  void dispose() {
    _otpController.dispose();
    _timer?.cancel();
    super.dispose();
  }

  void _startTimer() {
    setState(() {
      _secondsLeft = AppConstants.OTP_RESEND_SECONDS;
      _canResend = false;
    });
    _timer?.cancel();
    _timer = Timer.periodic(const Duration(seconds: 1), (timer) {
      if (_secondsLeft <= 1) {
        timer.cancel();
        setState(() => _canResend = true);
      } else {
        setState(() => _secondsLeft--);
      }
    });
  }

  Future<void> _verify() async {
    if (_otpController.text.length != AppConstants.OTP_LENGTH) {
      ErrorSnackbar.showError(context, 'Ingresa los 6 dígitos del código');
      return;
    }

    final success = await ref.read(authProvider.notifier).verifyPhone(
          widget.phone,
          _otpController.text,
          widget.purpose,
        );

    if (!mounted) return;

    if (success) {
      if (widget.purpose == 'phone_verify') {
        context.go('/login');
      } else if (widget.purpose == 'forgot_password') {
        context.push(
          Uri(
            path: '/reset-password',
            queryParameters: {'phone': widget.phone},
          ).toString(),
        );
      }
    } else {
      final error = ref.read(authProvider).error?.toString() ?? 'Código incorrecto';
      ErrorSnackbar.showError(context, error);
      _otpController.clear();
    }
  }

  Future<void> _resend() async {
    if (!_canResend) return;
    await ref.read(authProvider.notifier).sendOTP(widget.phone, widget.purpose);
    _startTimer();
  }

  String get _maskedPhone {
    if (widget.phone.length > 4) {
      return '***${widget.phone.substring(widget.phone.length - 4)}';
    }
    return widget.phone;
  }

  @override
  Widget build(BuildContext context) {
    final isLoading = ref.watch(authProvider).isLoading;

    final defaultPinTheme = PinTheme(
      width: 52,
      height: 60,
      textStyle: AppTextStyles.headingMedium,
      decoration: BoxDecoration(
        color: AppColors.surface,
        borderRadius: BorderRadius.circular(12),
        border: Border.all(color: AppColors.border),
      ),
    );

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
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.stretch,
            children: [
              const SizedBox(height: 16),
              Text('Verificar número', style: AppTextStyles.displayMedium),
              const SizedBox(height: 8),
              Text(
                'Ingresa el código de 6 dígitos enviado a $_maskedPhone',
                style: AppTextStyles.bodyMedium.copyWith(
                  color: AppColors.textSecondary,
                ),
              ),
              const SizedBox(height: 40),
              Center(
                child: Pinput(
                  controller: _otpController,
                  length: AppConstants.OTP_LENGTH,
                  defaultPinTheme: defaultPinTheme,
                  focusedPinTheme: defaultPinTheme.copyDecorationWith(
                    border: Border.all(color: AppColors.primary, width: 2),
                  ),
                  errorPinTheme: defaultPinTheme.copyDecorationWith(
                    border: Border.all(color: AppColors.error),
                  ),
                  onCompleted: (_) => _verify(),
                  keyboardType: TextInputType.number,
                ),
              ),
              const SizedBox(height: 32),
              PrimaryButton(
                text: 'Verificar',
                onPressed: _verify,
                isLoading: isLoading,
              ),
              const SizedBox(height: 24),
              Center(
                child: _canResend
                    ? TextButton(
                        onPressed: _resend,
                        child: Text(
                          'Reenviar código',
                          style: AppTextStyles.labelLarge.copyWith(
                            color: AppColors.primary,
                          ),
                        ),
                      )
                    : Text(
                        'Reenviar en $_secondsLeft segundos',
                        style: AppTextStyles.labelMedium,
                        textAlign: TextAlign.center,
                      ),
              ),
            ],
          ),
        ),
      ),
    );
  }
}
