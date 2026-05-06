import 'dart:io';

import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../../../core/theme/app_colors.dart';
import '../../../../core/theme/app_text_styles.dart';
import '../../../../shared/widgets/primary_button.dart';
import '../../domain/providers/profile_provider.dart';
import '../widgets/document_upload_tile.dart';

/// Pantalla de documentos del conductor (licencia, SOAT, etc).
class DriverDocsScreen extends ConsumerStatefulWidget {
  const DriverDocsScreen({super.key});

  @override
  ConsumerState<DriverDocsScreen> createState() => _DriverDocsScreenState();
}

class _DriverDocsScreenState extends ConsumerState<DriverDocsScreen> {
  final Map<String, File?> _files = {
    'dni_front': null,
    'dni_back': null,
    'license': null,
    'soat': null,
    'selfie': null,
    'property_card': null,
  };

  bool _isLoading = false;
  String? _errorMessage;

  static const _requiredDocs = {'dni_front', 'dni_back', 'license', 'soat', 'selfie'};

  bool get _requiredComplete =>
      _requiredDocs.every((k) => _files[k] != null);

  Future<void> _saveDocs() async {
    setState(() {
      _isLoading = true;
      _errorMessage = null;
    });

    final repository = ref.read(profileRepositoryProvider);
    final toUpload = _files.entries.where((e) => e.value != null);

    try {
      for (final entry in toUpload) {
        await repository.uploadDocument(
          documentType: entry.key,
          file: entry.value!,
        );
      }

      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(content: Text('Documentos enviados. Tu perfil está en revisión.')),
        );
      }
    } catch (e) {
      setState(() => _errorMessage = e.toString().replaceFirst('Exception: ', ''));
    } finally {
      if (mounted) setState(() => _isLoading = false);
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
            if (_errorMessage != null) ...[
              const SizedBox(height: 12),
              Container(
                padding: const EdgeInsets.all(12),
                decoration: BoxDecoration(
                  color: AppColors.errorLight,
                  borderRadius: BorderRadius.circular(12),
                ),
                child: Text(_errorMessage!, style: AppTextStyles.bodySmall.copyWith(color: AppColors.error)),
              ),
            ],
            const SizedBox(height: 24),
            Text('Documentos requeridos', style: AppTextStyles.labelLarge),
            const SizedBox(height: 16),
            _buildTile('dni_front', 'DNI (frontal)', 'Parte delantera de tu DNI', required: true),
            _buildTile('dni_back', 'DNI (reverso)', 'Parte trasera de tu DNI', required: true),
            _buildTile('license', 'Licencia de conducir', 'Licencia vigente', required: true),
            _buildTile('soat', 'SOAT', 'Seguro vigente', required: true),
            _buildTile('selfie', 'Selfie con DNI', 'Sosteniendo tu documento', required: true),
            const SizedBox(height: 8),
            Text('Opcional', style: AppTextStyles.labelLarge),
            const SizedBox(height: 16),
            _buildTile('property_card', 'Tarjeta de propiedad', 'Del vehículo'),
            const SizedBox(height: 32),
            PrimaryButton(
              text: 'Enviar documentos',
              isLoading: _isLoading,
              onPressed: _requiredComplete ? _saveDocs : null,
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildTile(String key, String title, String subtitle, {bool required = false}) {
    final file = _files[key];
    return DocumentUploadTile(
      title: title,
      subtitle: subtitle,
      file: file,
      isRequired: required,
      onFileSelected: (f) => setState(() => _files[key] = f),
      onRemove: file != null ? () => setState(() => _files[key] = null) : null,
    );
  }
}