import 'package:flutter/material.dart';

import '../../../../core/theme/app_colors.dart';
import '../../../../core/theme/app_text_styles.dart';
import '../../../auth/data/models/user_model.dart';

/// Header de perfil con avatar, nombre y rating.
class ProfileHeader extends StatelessWidget {
  final UserModel user;
  final VoidCallback? onEditTap;

  const ProfileHeader({
    super.key,
    required this.user,
    this.onEditTap,
  });

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.all(20),
      decoration: BoxDecoration(
        gradient: LinearGradient(
          colors: [AppColors.primary, AppColors.primaryLight],
          begin: Alignment.topCenter,
          end: Alignment.bottomCenter,
        ),
        borderRadius: const BorderRadius.only(
          bottomLeft: Radius.circular(30),
          bottomRight: Radius.circular(30),
        ),
      ),
      child: Column(
        children: [
          CircleAvatar(
            radius: 45,
            backgroundColor: Colors.white,
            child: user.avatarUrl != null
                ? CircleAvatar(radius: 42, backgroundImage: NetworkImage(user.avatarUrl!))
                : Text(
                    user.initials,
                    style: AppTextStyles.headingMedium.copyWith(color: AppColors.primary),
                  ),
          ),
          const SizedBox(height: 12),
          Text(user.fullName, style: AppTextStyles.headingSmall.copyWith(color: Colors.white)),
          const SizedBox(height: 4),
          Text(user.email, style: AppTextStyles.bodySmall.copyWith(color: Colors.white70)),
          const SizedBox(height: 12),
          Row(
            mainAxisAlignment: MainAxisAlignment.center,
            children: [
              _buildStat('Viajes', user.totalTrips.toString()),
              Container(width: 1, height: 20, color: Colors.white30, margin: const EdgeInsets.symmetric(horizontal: 16)),
              _buildStat('Rating', user.rating.toStringAsFixed(1)),
              if (user.isDriver) ...[
                Container(width: 1, height: 20, color: Colors.white30, margin: const EdgeInsets.symmetric(horizontal: 16)),
                _buildStat('Conductor', '✓'),
              ],
            ],
          ),
          const SizedBox(height: 16),
          if (onEditTap != null)
            OutlinedButton.icon(
              onPressed: onEditTap,
              icon: const Icon(Icons.edit, size: 16),
              label: const Text('Editar perfil'),
              style: OutlinedButton.styleFrom(
                foregroundColor: Colors.white,
                side: const BorderSide(color: Colors.white),
              ),
            ),
        ],
      ),
    );
  }

  Widget _buildStat(String label, String value) {
    return Column(
      children: [
        Text(value, style: AppTextStyles.labelLarge.copyWith(color: Colors.white)),
        Text(label, style: AppTextStyles.labelSmall.copyWith(color: Colors.white70)),
      ],
    );
  }
}