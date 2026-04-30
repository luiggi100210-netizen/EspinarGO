import 'dart:io';

import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../../../core/theme/app_colors.dart';
import '../../../../core/theme/app_text_styles.dart';
import '../../../../shared/widgets/primary_button.dart';
import '../widgets/document_upload_tile.dart';

/// Pantalla de documentos del conductor (licencia, SOAT, etc).
class DriverDocsScreen extends ConsumerStatefulWidget {
  const DriverDocsScreen({super.key});

  @override
  ConsumerState<DriverDocsScreen> createState() => _DriverDocsScreenState();
}

class _DriverDocsScreenState extends ConsumerState<DriverDocsScreen> {
  File? _licenseFile;
  File? _soatFile;
  File? _vehicleFile;

  bool _isLoading = false;

  Future<void> _saveDocs() async {
    setState(() => _isLoading = true);
    await Future.delayed(const Duration(seconds: 1));
    if (mounted) {
      setState(() => _isLoading = false);
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('Documentos guardados correctamente')),
      );
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('Mis documentos'),
        backgroundColor: Colors.transparent,
      ),
      body: SingleChildScrollView(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Container(
              padding: const EdgeInsets.all(12),
              decoration: BoxDecoration(
                color: AppColors.infoLight,
                borderRadius: BorderRadius.circular(12),
              ),
              child: Row(
                children: [
                  const Icon(Icons.info_outline, color: AppColors.info),
                  const SizedBox(width: 12),
                  Expanded(
                    child: Text(
                      'Sube tus documentos para completar tu registro como conductor',
                      style: AppTextStyles.bodySmall,
                    ),
                  ),
                ],
              ),
            ),
            const SizedBox(height: 24),
            Text('Documentos requeridos', style: AppTextStyles.labelLarge),
            const SizedBox(height: 16),
            DocumentUploadTile(
              title: 'Licencia de conducir',
              subtitle: 'Frontal y reverso',
              file: _licenseFile,
              isRequired: true,
              onFileSelected: (file) => setState(() => _licenseFile = file),
              onRemove: _licenseFile != null ? () => setState(() => _licenseFile = null) : null,
            ),
            DocumentUploadTile(
              title: 'SOAT',
              subtitle: 'Vigente',
              file: _soatFile,
              isRequired: true,
              onFileSelected: (file) => setState(() => _soatFile = file),
              onRemove: _soatFile != null ? () => setState(() => _soatFile = null) : null,
            ),
            DocumentUploadTile(
              title: 'Tarjeta de propiedad',
              subtitle: 'Del vehículo',
              file: _vehicleFile,
              isRequired: true,
              onFileSelected: (file) => setState(() => _vehicleFile = file),
              onRemove: _vehicleFile != null ? () => setState(() => _vehicleFile = null) : null,
            ),
            const SizedBox(height: 32),
            PrimaryButton(
              text: 'Guardar documentos',
              isLoading: _isLoading,
              onPressed: _licenseFile != null && _soatFile != null && _vehicleFile != null ? _saveDocs : null,
            ),
          ],
        ),
      ),
    );
  }
}