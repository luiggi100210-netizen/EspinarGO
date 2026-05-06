import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../../../core/providers.dart';
import '../../../auth/domain/providers/auth_provider.dart';
import '../../data/repositories/profile_repository.dart';
import 'profile_state.dart';

/// Provider del repositorio de perfil.
final profileRepositoryProvider = Provider<ProfileRepository>((ref) {
  final dioClient = ref.watch(dioClientProvider);
  return ProfileRepository(dioClient: dioClient);
});

/// Provider principal del perfil.
final profileProvider = AsyncNotifierProvider<ProfileNotifier, ProfileState>(() {
  return ProfileNotifier();
});

/// Notificador del perfil de usuario.
class ProfileNotifier extends AsyncNotifier<ProfileState> {
  @override
  Future<ProfileState> build() async {
    final repository = ref.read(profileRepositoryProvider);
    final user = await repository.getProfile();
    return ProfileState(user: user);
  }

  /// Actualiza nombre y teléfono del usuario.
  /// Retorna true si fue exitoso.
  Future<bool> updateProfile({
    required String fullName,
    required String phone,
  }) async {
    final current = state.valueOrNull;
    if (current == null) return false;

    state = AsyncValue.data(current.copyWith(isLoading: true));

    try {
      final repository = ref.read(profileRepositoryProvider);
      final updatedUser = await repository.updateProfile(
        fullName: fullName,
        phoneNumber: phone,
      );

      state = AsyncValue.data(ProfileState(user: updatedUser));

      // Sincronizar con authProvider para mantener el usuario global al día.
      ref.read(authProvider.notifier).updateUser(updatedUser);

      return true;
    } catch (e) {
      state = AsyncValue.data(
        current.copyWith(
          isLoading: false,
          errorMessage: e.toString().replaceFirst('Exception: ', ''),
        ),
      );
      return false;
    }
  }
}
