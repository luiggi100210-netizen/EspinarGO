import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import '../../../../core/theme/app_colors.dart';
import '../../../../shared/widgets/loading_indicator.dart';
import '../../../auth/domain/providers/auth_provider.dart';
import '../../domain/providers/profile_provider.dart';
import '../widgets/profile_header.dart';
import '../widgets/profile_menu_item.dart';

/// Pantalla principal del perfil de usuario.
class ProfileScreen extends ConsumerWidget {
  const ProfileScreen({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final state = ref.watch(profileProvider);
    final profileState = state.valueOrNull;

    if (profileState == null) {
      return const Scaffold(body: LoadingIndicator());
    }

    final user = profileState.user;

    return Scaffold(
      body: CustomScrollView(
        slivers: [
          SliverToBoxAdapter(
            child: ProfileHeader(
              user: user,
              onEditTap: () => context.push('/profile/edit'),
            ),
          ),
          SliverToBoxAdapter(
            child: Padding(
              padding: const EdgeInsets.all(16),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text('Mi cuenta', style: Theme.of(context).textTheme.titleMedium),
                  const SizedBox(height: 8),
                  Card(
                    child: Column(
                      children: [
                        ProfileMenuItem(
                          icon: Icons.history,
                          title: 'Historial de viajes',
                          onTap: () => context.push('/trips/history'),
                        ),
                        ProfileMenuItem(
                          icon: Icons.inventory_2,
                          title: 'Encomiendas',
                          onTap: () => context.push('/packages'),
                        ),
                        ProfileMenuItem(
                          icon: Icons.favorite,
                          title: 'Lugares guardados',
                          onTap: () {},
                        ),
                        ProfileMenuItem(
                          icon: Icons.payment,
                          title: 'Métodos de pago',
                          onTap: () {},
                        ),
                      ],
                    ),
                  ),
                  const SizedBox(height: 24),
                  if (user.isDriver) ...[
                    Text('Conductor', style: Theme.of(context).textTheme.titleMedium),
                    const SizedBox(height: 8),
                    Card(
                      child: Column(
                        children: [
                          ProfileMenuItem(
                            icon: Icons.directions_car,
                            title: 'Mi vehículo',
                            onTap: () {},
                          ),
                          ProfileMenuItem(
                            icon: Icons.description,
                            title: 'Mis documentos',
                            onTap: () => context.push('/profile/driver-docs'),
                          ),
                          ProfileMenuItem(
                            icon: Icons.analytics,
                            title: 'Estadísticas',
                            onTap: () {},
                          ),
                        ],
                      ),
                    ),
                    const SizedBox(height: 24),
                  ],
                  Text('Soporte', style: Theme.of(context).textTheme.titleMedium),
                  const SizedBox(height: 8),
                  Card(
                    child: Column(
                      children: [
                        ProfileMenuItem(
                          icon: Icons.help,
                          title: 'Ayuda',
                          onTap: () => context.push('/profile/help'),
                        ),
                        ProfileMenuItem(
                          icon: Icons.settings,
                          title: 'Configuración',
                          onTap: () => context.push('/profile/settings'),
                        ),
                      ],
                    ),
                  ),
                  const SizedBox(height: 24),
                  Center(
                    child: TextButton.icon(
                      onPressed: () => _showLogoutDialog(context, ref),
                      icon: const Icon(Icons.logout, color: AppColors.error),
                      label: const Text('Cerrar sesión', style: TextStyle(color: AppColors.error)),
                    ),
                  ),
                  const SizedBox(height: 16),
                  Center(
                    child: Text('EspinarGo v1.0.0', style: Theme.of(context).textTheme.bodySmall),
                  ),
                ],
              ),
            ),
          ),
        ],
      ),
    );
  }

  void _showLogoutDialog(BuildContext context, WidgetRef ref) {
    showDialog(
      context: context,
      builder: (context) => AlertDialog(
        title: const Text('Cerrar sesión'),
        content: const Text('¿Estás seguro de que quieres cerrar sesión?'),
        actions: [
          TextButton(onPressed: () => Navigator.pop(context), child: const Text('Cancelar')),
          TextButton(
            onPressed: () async {
              Navigator.pop(context);
              await ref.read(authProvider.notifier).logout();
            },
            style: TextButton.styleFrom(foregroundColor: AppColors.error),
            child: const Text('Cerrar sesión'),
          ),
        ],
      ),
    );
  }
}