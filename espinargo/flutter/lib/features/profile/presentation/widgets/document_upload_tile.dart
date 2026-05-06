import 'dart:io';

import 'package:flutter/material.dart';
import 'package:image_picker/image_picker.dart';

import '../../../../core/theme/app_colors.dart';
import '../../../../core/theme/app_text_styles.dart';

/// Tile para subir documentos (licencia, SOAT, etc).
class DocumentUploadTile extends StatelessWidget {
  final String title;
  final String? subtitle;
  final File? file;
  final String? imageUrl;
  final ValueChanged<File?> onFileSelected;
  final VoidCallback? onRemove;
  final bool isRequired;

  const DocumentUploadTile({
    super.key,
    required this.title,
    this.subtitle,
    this.file,
    this.imageUrl,
    required this.onFileSelected,
    this.onRemove,
    this.isRequired = false,
  });

  bool get hasFile => file != null || imageUrl != null;

  @override
  Widget build(BuildContext context) {
    return Container(
      margin: const EdgeInsets.only(bottom: 12),
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        color: Colors.white,
        borderRadius: BorderRadius.circular(12),
        border: Border.all(color: hasFile ? AppColors.success : AppColors.border),
      ),
      child: hasFile ? _buildPreview() : _buildUploadButton(context),
    );
  }

  Widget _buildPreview() {
    final displayUrl = imageUrl ?? (file != null ? file!.path : null);
    return Row(
      children: [
        ClipRRect(
          borderRadius: BorderRadius.circular(8),
          child: displayUrl != null
              ? Image.file(
                  File(displayUrl),
                  width: 60,
                  height: 60,
                  fit: BoxFit.cover,
                  errorBuilder: (_, __, ___) => Container(
                    width: 60,
                    height: 60,
                    color: AppColors.border,
                    child: const Icon(Icons.image_not_supported),
                  ),
                )
              : Container(
                  width: 60,
                  height: 60,
                  color: AppColors.border,
                  child: const Icon(Icons.description),
                ),
        ),
        const SizedBox(width: 12),
        Expanded(
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Text(title, style: AppTextStyles.labelLarge),
              const SizedBox(height: 2),
              Text(
                file?.path.split('/').last ?? 'Documento subido',
                style: AppTextStyles.bodySmall,
                maxLines: 1,
                overflow: TextOverflow.ellipsis,
              ),
            ],
          ),
        ),
        IconButton(
          icon: const Icon(Icons.check_circle, color: AppColors.success),
          onPressed: null,
        ),
        if (onRemove != null)
          IconButton(
            icon: const Icon(Icons.close, color: AppColors.error),
            onPressed: onRemove,
          ),
      ],
    );
  }

  Widget _buildUploadButton(BuildContext context) {
    return InkWell(
      onTap: () => _showPicker(context),
      borderRadius: BorderRadius.circular(12),
      child: Column(
        children: [
          Icon(
            Icons.cloud_upload_outlined,
            size: 40,
            color: AppColors.textSecondary,
          ),
          const SizedBox(height: 8),
          Row(
            mainAxisAlignment: MainAxisAlignment.center,
            children: [
              Text(title, style: AppTextStyles.labelLarge),
              if (isRequired) ...[
                const SizedBox(width: 4),
                const Text('*', style: TextStyle(color: AppColors.error)),
              ],
            ],
          ),
          if (subtitle != null) ...[
            const SizedBox(height: 4),
            Text(subtitle!, style: AppTextStyles.bodySmall, textAlign: TextAlign.center),
          ],
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
              onTap: () async {
                Navigator.pop(context);
                final picked = await ImagePicker().pickImage(source: ImageSource.camera);
                if (picked != null) onFileSelected(File(picked.path));
              },
            ),
            ListTile(
              leading: const Icon(Icons.photo_library),
              title: const Text('Galería'),
              onTap: () async {
                Navigator.pop(context);
                final picked = await ImagePicker().pickImage(source: ImageSource.gallery);
                if (picked != null) onFileSelected(File(picked.path));
              },
            ),
          ],
        ),
      ),
    );
  }
}