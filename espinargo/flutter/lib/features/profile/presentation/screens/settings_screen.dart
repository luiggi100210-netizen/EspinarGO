import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import '../../../../core/theme/app_colors.dart';
import '../../../../core/theme/app_text_styles.dart';
import '../widgets/profile_menu_item.dart';

/// Pantalla de configuración de la app.
class SettingsScreen extends ConsumerWidget {
  const SettingsScreen({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('Configuración'),
        backgroundColor: Colors.transparent,
      ),
      body: ListView(
        padding: const EdgeInsets.all(16),
        children: [
          Text('Preferencias', style: AppTextStyles.labelLarge),
          const SizedBox(height: 8),
          ProfileMenuItem(
            icon: Icons.notifications,
            title: 'Notificaciones',
            subtitle: 'Activas',
            onTap: () {},
          ),
          ProfileMenuItem(
            icon: Icons.language,
            title: 'Idioma',
            subtitle: 'Español',
            onTap: () {},
          ),
          ProfileMenuItem(
            icon: Icons.location_on,
            title: 'Ubicación',
            subtitle: 'Siempre',
            onTap: () {},
          ),
          const SizedBox(height: 24),
          Text('Privacidad', style: AppTextStyles.labelLarge),
          const SizedBox(height: 8),
          ProfileMenuItem(
            icon: Icons.lock,
            title: 'Cambiar contraseña',
            onTap: () {},
          ),
          ProfileMenuItem(
            icon: Icons.security,
            title: 'Privacidad',
            onTap: () {},
          ),
          ProfileMenuItem(
            icon: Icons.delete_forever,
            title: 'Eliminar cuenta',
            iconColor: AppColors.error,
            onTap: () => _showDeleteDialog(context),
          ),
          const SizedBox(height: 24),
          Text('Otros', style: AppTextStyles.labelLarge),
          const SizedBox(height: 8),
          ProfileMenuItem(
            icon: Icons.help,
            title: 'Ayuda',
            onTap: () => context.push('/profile/help'),
          ),
          ProfileMenuItem(
            icon: Icons.info,
            title: 'Acerca de',
            onTap: () {},
          ),
          ProfileMenuItem(
            icon: Icons.description,
            title: 'Términos y condiciones',
            onTap: () {},
          ),
          ProfileMenuItem(
            icon: Icons.privacy_tip,
            title: 'Política de privacidad',
            onTap: () {},
          ),
        ],
      ),
    );
  }

  void _showDeleteDialog(BuildContext context) {
    showDialog(
      context: context,
      builder: (context) => AlertDialog(
        title: const Text('¿Eliminar cuenta?'),
        content: const Text('Esta acción no se puede revertir. Perderás todos tus datos.'),
        actions: [
          TextButton(onPressed: () => Navigator.pop(context), child: const Text('Cancelar')),
          TextButton(
            onPressed: () {},
            style: TextButton.styleFrom(foregroundColor: AppColors.error),
            child: const Text('Eliminar'),
          ),
        ],
      ),
    );
  }
}