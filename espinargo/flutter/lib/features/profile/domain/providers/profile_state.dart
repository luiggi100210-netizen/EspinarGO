import '../../../auth/data/models/user_model.dart';

/// Estado del perfil de usuario.
class ProfileState {
  final UserModel user;
  final bool isLoading;
  final String? errorMessage;

  const ProfileState({
    required this.user,
    this.isLoading = false,
    this.errorMessage,
  });

  ProfileState copyWith({
    UserModel? user,
    bool? isLoading,
    String? errorMessage,
  }) {
    return ProfileState(
      user: user ?? this.user,
      isLoading: isLoading ?? this.isLoading,
      errorMessage: errorMessage,
    );
  }
}
