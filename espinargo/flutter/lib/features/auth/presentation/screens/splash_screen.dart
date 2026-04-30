import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import '../../../../core/theme/app_colors.dart';
import '../../../../shared/widgets/espinargo_logo.dart';
import '../../domain/providers/auth_provider.dart';

/// Pantalla inicial — verifica sesión activa y redirige.
class SplashScreen extends ConsumerWidget {
  const SplashScreen({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final authAsync = ref.watch(authProvider);

    authAsync.whenOrNull(
      data: (authState) {
        WidgetsBinding.instance.addPostFrameCallback((_) async {
          if (!context.mounted) return;

          if (authState.isAuthenticated) {
            context.go(authState.isDriver ? '/driver/dashboard' : '/home');
          } else {
            final isFirst = await ref.read(isFirstLaunchProvider.future);
            if (!context.mounted) return;
            context.go(isFirst ? '/onboarding' : '/login');
          }
        });
      },
    );

    return Scaffold(
      backgroundColor: AppColors.primary,
      body: const Center(
        child: EspinarGoLogo(size: 'large', showTagline: true),
      ),
    );
  }
}
