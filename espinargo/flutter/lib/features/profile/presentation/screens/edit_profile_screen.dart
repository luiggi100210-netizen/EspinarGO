import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import '../../../../shared/widgets/primary_button.dart';
import '../../../auth/presentation/widgets/auth_text_field.dart';
import '../../domain/providers/profile_provider.dart';
import '../widgets/avatar_picker.dart';

/// Pantalla para editar el perfil del usuario.
class EditProfileScreen extends ConsumerStatefulWidget {
  const EditProfileScreen({super.key});

  @override
  ConsumerState<EditProfileScreen> createState() => _EditProfileScreenState();
}

class _EditProfileScreenState extends ConsumerState<EditProfileScreen> {
  final _formKey = GlobalKey<FormState>();
  late TextEditingController _nameController;
  late TextEditingController _phoneController;

  @override
  void initState() {
    super.initState();
    final user = ref.read(profileProvider).valueOrNull?.user;
    _nameController = TextEditingController(text: user?.fullName ?? '');
    _phoneController = TextEditingController(text: user?.phoneNumber ?? '');
  }

  @override
  void dispose() {
    _nameController.dispose();
    _phoneController.dispose();
    super.dispose();
  }

  Future<void> _saveProfile() async {
    if (!_formKey.currentState!.validate()) return;

    final success = await ref.read(profileProvider.notifier).updateProfile(
          fullName: _nameController.text,
          phone: _phoneController.text,
        );

    if (success && mounted) {
      context.pop();
    }
  }

  @override
  Widget build(BuildContext context) {
    final state = ref.watch(profileProvider);
    final profileState = state.valueOrNull;
    final isLoading = profileState?.isLoading ?? false;

    return Scaffold(
      appBar: AppBar(
        title: const Text('Editar perfil'),
        backgroundColor: Colors.transparent,
      ),
      body: SingleChildScrollView(
        padding: const EdgeInsets.all(16),
        child: Form(
          key: _formKey,
          child: Column(
            children: [
              Center(
                child: AvatarPicker(
                  currentImageUrl: profileState?.user.avatarUrl,
                  onImageSelected: (file) {},
                ),
              ),
              const SizedBox(height: 32),
              AuthTextField(
                controller: _nameController,
                label: 'Nombre completo',
                hint: 'Juan Quispe',
                prefixIcon: Icons.person,
                validator: (v) => v?.isEmpty == true ? 'Ingresa tu nombre' : null,
              ),
              const SizedBox(height: 16),
              AuthTextField(
                controller: _phoneController,
                label: 'Teléfono',
                hint: '987 654 321',
                prefixIcon: Icons.phone,
                keyboardType: TextInputType.phone,
                validator: (v) => v?.isEmpty == true ? 'Ingresa tu teléfono' : null,
              ),
              const SizedBox(height: 32),
              PrimaryButton(
                text: 'Guardar cambios',
                isLoading: isLoading,
                onPressed: _saveProfile,
              ),
            ],
          ),
        ),
      ),
    );
  }
}