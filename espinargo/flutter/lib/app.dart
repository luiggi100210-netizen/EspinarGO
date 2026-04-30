import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import 'core/theme/app_theme.dart';
import 'core/theme/app_colors.dart';
import 'features/home/presentation/screens/home_screen.dart';
import 'features/auth/presentation/screens/splash_screen.dart';
import 'features/auth/presentation/screens/onboarding_screen.dart';
import 'features/auth/presentation/screens/role_selection_screen.dart';
import 'features/auth/presentation/screens/register_screen.dart';
import 'features/auth/presentation/screens/otp_screen.dart';
import 'features/auth/presentation/screens/login_screen.dart';
import 'features/auth/presentation/screens/forgot_password_screen.dart';
import 'features/auth/presentation/screens/reset_password_screen.dart';
import 'features/trips/presentation/screens/propose_price_screen.dart';
import 'features/trips/presentation/screens/waiting_drivers_screen.dart';
import 'features/trips/presentation/screens/trip_offers_screen.dart';
import 'features/trips/presentation/screens/trip_active_screen.dart';
import 'features/trips/presentation/screens/trip_completed_screen.dart';
import 'features/trips/presentation/screens/trip_history_screen.dart';
import 'features/driver/presentation/screens/driver_dashboard_screen.dart';
import 'features/driver/presentation/screens/driver_earnings_screen.dart';
import 'features/driver/presentation/screens/driver_trip_active_screen.dart';
import 'features/driver/presentation/screens/driver_trip_completed_screen.dart';
import 'features/packages/presentation/screens/packages_screen.dart';
import 'features/packages/presentation/screens/track_package_screen.dart';
import 'features/packages/presentation/screens/send_package_screen.dart';
import 'features/packages/presentation/screens/package_detail_screen.dart';
import 'features/profile/presentation/screens/profile_screen.dart';
import 'features/profile/presentation/screens/edit_profile_screen.dart';
import 'features/profile/presentation/screens/driver_docs_screen.dart';
import 'features/profile/presentation/screens/settings_screen.dart';
import 'features/profile/presentation/screens/help_screen.dart';

/// Configuración de GoRouter con todas las rutas de la app.
final appRouter = GoRouter(
  initialLocation: '/',
  routes: [
    // Pantalla de splash - verificación de sesión
    GoRoute(
      path: '/',
      name: 'splash',
      builder: (context, state) => const SplashScreen(),
    ),
    // Onboarding - primer lanzamiento
    GoRoute(
      path: '/onboarding',
      name: 'onboarding',
      builder: (context, state) => const OnboardingScreen(),
    ),
    // Selección de rol
    GoRoute(
      path: '/role-selection',
      name: 'roleSelection',
      builder: (context, state) => const RoleSelectionScreen(),
    ),
    // Registro
    GoRoute(
      path: '/register',
      name: 'register',
      builder: (context, state) {
        final role = state.uri.queryParameters['role'] ?? 'passenger';
        return RegisterScreen(role: role);
      },
    ),
    // Verificación OTP
    GoRoute(
      path: '/otp',
      name: 'otp',
      builder: (context, state) {
        final phone = state.uri.queryParameters['phone'] ?? '';
        final purpose = state.uri.queryParameters['purpose'] ?? 'phone_verify';
        return OTPScreen(phone: phone, purpose: purpose);
      },
    ),
    // Login
    GoRoute(
      path: '/login',
      name: 'login',
      builder: (context, state) => const LoginScreen(),
    ),
    // Recuperar contraseña
    GoRoute(
      path: '/forgot-password',
      name: 'forgotPassword',
      builder: (context, state) => const ForgotPasswordScreen(),
    ),
    // Nueva contraseña
    GoRoute(
      path: '/reset-password',
      name: 'resetPassword',
      builder: (context, state) {
        final phone = state.uri.queryParameters['phone'] ?? '';
        return ResetPasswordScreen(phone: phone);
      },
    ),
    // Home del pasajero
    GoRoute(
      path: '/home',
      name: 'home',
      builder: (context, state) => const HomeScreen(),
    ),
    // Driver dashboard
    GoRoute(
      path: '/driver/dashboard',
      name: 'driverDashboard',
      builder: (context, state) => const DriverDashboardScreen(),
    ),
    // Driver trip active
    GoRoute(
      path: '/driver/trip-active',
      name: 'driverTripActive',
      builder: (context, state) => const DriverTripActiveScreen(),
    ),
    // Driver trip completed
    GoRoute(
      path: '/driver/trip-completed',
      name: 'driverTripCompleted',
      builder: (context, state) => const DriverTripCompletedScreen(),
    ),
    // Driver earnings
    GoRoute(
      path: '/driver/earnings',
      name: 'driverEarnings',
      builder: (context, state) => const DriverEarningsScreen(),
    ),
    // Packages (Encomiendas)
    GoRoute(
      path: '/packages',
      name: 'packages',
      builder: (context, state) => const PackagesScreen(),
    ),
    GoRoute(
      path: '/packages/track',
      name: 'trackPackage',
      builder: (context, state) {
        final code = state.uri.queryParameters['code'];
        return TrackPackageScreen(initialCode: code);
      },
    ),
    GoRoute(
      path: '/packages/send',
      name: 'sendPackage',
      builder: (context, state) => const SendPackageScreen(),
    ),
    GoRoute(
      path: '/packages/detail/:code',
      name: 'packageDetail',
      builder: (context, state) {
        final code = state.pathParameters['code'] ?? '';
        return PackageDetailScreen(trackingCode: code);
      },
    ),
    // Profile (Perfil)
    GoRoute(
      path: '/profile',
      name: 'profile',
      builder: (context, state) => const ProfileScreen(),
    ),
    GoRoute(
      path: '/profile/edit',
      name: 'editProfile',
      builder: (context, state) => const EditProfileScreen(),
    ),
    GoRoute(
      path: '/profile/driver-docs',
      name: 'driverDocs',
      builder: (context, state) => const DriverDocsScreen(),
    ),
    GoRoute(
      path: '/profile/settings',
      name: 'settings',
      builder: (context, state) => const SettingsScreen(),
    ),
    GoRoute(
      path: '/profile/help',
      name: 'help',
      builder: (context, state) => const HelpScreen(),
    ),
    // Proponer precio
    GoRoute(
      path: '/propose-price',
      name: 'proposePrice',
      builder: (context, state) {
        final routeJson = state.uri.queryParameters['routeJson'] ?? '{}';
        return ProposePriceScreen(routeJson: routeJson);
      },
    ),
    // Esperando conductores
    GoRoute(
      path: '/waiting-drivers',
      name: 'waitingDrivers',
      builder: (context, state) => const WaitingDriversScreen(),
    ),
    // Ofertas de conductores
    GoRoute(
      path: '/trip-offers',
      name: 'tripOffers',
      builder: (context, state) => const TripOffersScreen(),
    ),
    // Viaje activo
    GoRoute(
      path: '/trip-active',
      name: 'tripActive',
      builder: (context, state) => const TripActiveScreen(),
    ),
    // Viaje completado
    GoRoute(
      path: '/trip-completed',
      name: 'tripCompleted',
      builder: (context, state) => const TripCompletedScreen(),
    ),
    // Historial de viajes
    GoRoute(
      path: '/trips/history',
      name: 'tripHistory',
      builder: (context, state) => const TripHistoryScreen(),
    ),
  ],
  errorBuilder: (context, state) => Scaffold(
    backgroundColor: AppColors.background,
    body: Center(
      child: Column(
        mainAxisAlignment: MainAxisAlignment.center,
        children: [
          const Icon(
            Icons.error_outline,
            size: 64,
            color: AppColors.error,
          ),
          const SizedBox(height: 16),
          Text(
            'Página no encontrada',
            style: Theme.of(context).textTheme.headlineSmall,
          ),
          const SizedBox(height: 24),
          ElevatedButton(
            onPressed: () => context.go('/'),
            child: const Text('Volver al inicio'),
          ),
        ],
      ),
    ),
  ),
);

/// Widget principal de la app.
/// Configura Theme, Router, y GlobalProviders.
class EspinarGoApp extends ConsumerWidget {
  const EspinarGoApp({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    return MaterialApp.router(
      title: 'EspinarGo',
      debugShowCheckedModeBanner: false,
      theme: AppTheme.lightTheme,
      routerConfig: appRouter,
      locale: const Locale('es', 'PE'),
      supportedLocales: const [
        Locale('es', 'PE'),
        Locale('es', 'ES'),
      ],
      localizationsDelegates: const [
        DefaultMaterialLocalizations.delegate,
        DefaultWidgetsLocalizations.delegate,
      ],
    );
  }
}

/// Widget de error cuando algo falla.
class ErrorScreen extends StatelessWidget {
  final String message;
  final VoidCallback? onRetry;

  const ErrorScreen({
    super.key,
    required this.message,
    this.onRetry,
  });

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: AppColors.background,
      body: Center(
        child: Padding(
          padding: const EdgeInsets.all(24),
          child: Column(
            mainAxisAlignment: MainAxisAlignment.center,
            children: [
              const Icon(
                Icons.error_outline,
                size: 64,
                color: AppColors.error,
              ),
              const SizedBox(height: 16),
              Text(
                'Algo salió mal',
                style: Theme.of(context).textTheme.headlineSmall,
              ),
              const SizedBox(height: 8),
              Text(
                message,
                textAlign: TextAlign.center,
                style: Theme.of(context).textTheme.bodyMedium?.copyWith(
                  color: AppColors.textSecondary,
                ),
              ),
              if (onRetry != null) ...[
                const SizedBox(height: 24),
                ElevatedButton(
                  onPressed: onRetry,
                  child: const Text('Reintentar'),
                ),
              ],
            ],
          ),
        ),
      ),
    );
  }
}