import 'package:flutter/material.dart';

import '../../core/theme/app_colors.dart';
import '../../core/theme/app_text_styles.dart';
import '../../core/utils/formatters.dart';
import '../../features/auth/data/models/user_model.dart';

/// Drawer lateral con info del usuario y navegación.
class AppDrawer extends StatelessWidget {
  final UserModel user;
  final VoidCallback onLogout;

  const AppDrawer({
    super.key,
    required this.user,
    required this.onLogout,
  });

  @override
  Widget build(BuildContext context) {
    return Drawer(
      child: Column(
        children: [
          // Header del drawer
          _buildHeader(),
          // Opciones de navegación
          Expanded(
            child: ListView(
              padding: EdgeInsets.zero,
              children: [
                _buildNavItem(
                  icon: Icons.map_outlined,
                  label: 'Mis viajes',
                  onTap: () => Navigator.pop(context),
                ),
                _buildNavItem(
                  icon: Icons.inventory_2_outlined,
                  label: 'Mis encomiendas',
                  onTap: () => Navigator.pop(context),
                ),
                _buildNavItem(
                  icon: Icons.star_outline,
                  label: 'Mis calificaciones',
                  onTap: () => Navigator.pop(context),
                ),
                const Divider(height: 1),
                _buildNavItem(
                  icon: Icons.help_outline,
                  label: 'Centro de ayuda',
                  onTap: () => Navigator.pop(context),
                ),
                _buildNavItem(
                  icon: Icons.phone_outlined,
                  label: 'Contactar soporte',
                  onTap: () => Navigator.pop(context),
                ),
                const Divider(height: 1),
                _buildNavItem(
                  icon: Icons.logout,
                  label: 'Cerrar sesión',
                  onTap: () => _handleLogout(context),
                  textColor: AppColors.error,
                ),
              ],
            ),
          ),
          // Footer
          _buildFooter(),
        ],
      ),
    );
  }

  Widget _buildHeader() {
    return Container(
      width: double.infinity,
      padding: const EdgeInsets.fromLTRB(20, 60, 20, 20),
      color: AppColors.primary,
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          // Avatar
          CircleAvatar(
            radius: 32,
            backgroundColor: Colors.white.withOpacity(0.2),
            child: Text(
              user.initials,
              style: AppTextStyles.headingLarge.copyWith(
                color: Colors.white,
              ),
            ),
          ),
          const SizedBox(height: 12),
          // Nombre
          Text(
            user.fullName,
            style: AppTextStyles.headingMedium.copyWith(
              color: Colors.white,
            ),
          ),
          const SizedBox(height: 4),
          // Teléfono
          Text(
            Formatters.phone(user.phoneNumber),
            style: AppTextStyles.bodySmall.copyWith(
              color: Colors.white.withOpacity(0.8),
            ),
          ),
          const SizedBox(height: 8),
          // Badge de rol
          Container(
            padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 4),
            decoration: BoxDecoration(
              color: user.isDriver
                  ? AppColors.success.withOpacity(0.3)
                  : Colors.white.withOpacity(0.2),
              borderRadius: BorderRadius.circular(12),
            ),
            child: Text(
              user.isDriver ? 'Conductor' : 'Pasajero',
              style: AppTextStyles.labelSmall.copyWith(
                color: Colors.white,
                fontWeight: FontWeight.w600,
              ),
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildNavItem({
    required IconData icon,
    required String label,
    required VoidCallback onTap,
    Color? textColor,
  }) {
    return ListTile(
      leading: Icon(
        icon,
        color: textColor ?? AppColors.textSecondary,
      ),
      title: Text(
        label,
        style: AppTextStyles.bodyMedium.copyWith(
          color: textColor ?? AppColors.textPrimary,
        ),
      ),
      onTap: onTap,
      contentPadding: const EdgeInsets.symmetric(horizontal: 20),
      dense: true,
    );
  }

  Widget _buildFooter() {
    return Container(
      padding: const EdgeInsets.all(16),
      child: Column(
        children: [
          const Divider(),
          Text(
            'EspinarGo v1.0.0',
            style: AppTextStyles.labelSmall,
          ),
          const SizedBox(height: 4),
          Text(
            'Espinar · Cusco · Perú',
            style: AppTextStyles.labelSmall.copyWith(
              color: AppColors.textDisabled,
            ),
          ),
        ],
      ),
    );
  }

  void _handleLogout(BuildContext context) {
    showDialog(
      context: context,
      builder: (context) => AlertDialog(
        title: const Text('Cerrar sesión'),
        content: const Text('¿Estás seguro de que quieres cerrar sesión?'),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(context),
            child: const Text('Cancelar'),
          ),
          TextButton(
            onPressed: () {
              Navigator.pop(context);
              Navigator.pop(context);
              onLogout();
            },
            child: Text(
              'Cerrar',
              style: TextStyle(color: AppColors.error),
            ),
          ),
        ],
      ),
    );
  }
}