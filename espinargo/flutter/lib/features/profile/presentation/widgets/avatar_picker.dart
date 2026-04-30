import 'dart:io';

import 'package:flutter/material.dart';

import '../../../../core/theme/app_colors.dart';
import '../../../../core/theme/app_text_styles.dart';

/// Selector de avatar desde galería o cámara.
class AvatarPicker extends StatelessWidget {
  final String? currentImageUrl;
  final ValueChanged<File?> onImageSelected;

  const AvatarPicker({
    super.key,
    this.currentImageUrl,
    required this.onImageSelected,
  });

  @override
  Widget build(BuildContext context) {
    return GestureDetector(
      onTap: () => _showPicker(context),
      child: Stack(
        children: [
          CircleAvatar(
            radius: 50,
            backgroundColor: AppColors.packageLight,
            backgroundImage: currentImageUrl != null ? NetworkImage(currentImageUrl!) : null,
            child: currentImageUrl == null
                ? const Icon(Icons.person, size: 50, color: AppColors.package)
                : null,
          ),
          Positioned(
            bottom: 0,
            right: 0,
            child: Container(
              padding: const EdgeInsets.all(6),
              decoration: const BoxDecoration(
                color: AppColors.package,
                shape: BoxShape.circle,
              ),
              child: const Icon(Icons.camera_alt, size: 18, color: Colors.white),
            ),
          ),
        ],
      ),
    );
  }

  void _showPicker(BuildContext context) {
    showModalBottomSheet(
      context: context,
      builder: (context) => SafeArea(
        child: Wrap(
          children: [
            ListTile(
              leading: const Icon(Icons.camera_alt),
              title: const Text('Cámara'),
              onTap: () {
                Navigator.pop(context);
                onImageSelected(null);
              },
            ),
            ListTile(
              leading: const Icon(Icons.photo_library),
              title: const Text('Galería'),
              onTap: () {
                Navigator.pop(context);
                onImageSelected(null);
              },
            ),
            if (currentImageUrl != null)
              ListTile(
                leading: const Icon(Icons.delete, color: AppColors.error),
                title: const Text('Eliminar foto'),
                onTap: () {
                  Navigator.pop(context);
                  onImageSelected(null);
                },
              ),
          ],
        ),
      ),
    );
  }
}