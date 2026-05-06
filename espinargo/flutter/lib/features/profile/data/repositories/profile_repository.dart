import 'dart:io';

import 'package:dio/dio.dart';

import '../../../../core/constants/api_constants.dart';
import '../../../../core/network/dio_client.dart';
import '../../../auth/data/models/user_model.dart';

/// Repositorio de perfil de usuario.
class ProfileRepository {
  final DioClient _dioClient;

  ProfileRepository({required DioClient dioClient}) : _dioClient = dioClient;

  /// Obtiene el perfil del usuario autenticado.
  Future<UserModel> getProfile() async {
    try {
      final response = await _dioClient.get('${ApiConstants.AUTH}${ApiConstants.ME}');
      return UserModel.fromJson(response.data as Map<String, dynamic>);
    } on DioException catch (e) {
      throw Exception(_handleError(e));
    }
  }

  /// Actualiza el nombre completo y/o teléfono del usuario.
  Future<UserModel> updateProfile({
    required String fullName,
    required String phoneNumber,
  }) async {
    try {
      final response = await _dioClient.patch(
        '${ApiConstants.USERS}/profile',
        data: {
          'full_name': fullName,
          'phone_number': phoneNumber,
        },
      );
      return UserModel.fromJson(response.data as Map<String, dynamic>);
    } on DioException catch (e) {
      throw Exception(_handleError(e));
    }
  }

  /// Sube una nueva foto de perfil.
  Future<UserModel> uploadAvatar(File imageFile) async {
    try {
      final formData = FormData.fromMap({
        'file': await MultipartFile.fromFile(
          imageFile.path,
          filename: 'avatar.jpg',
        ),
      });
      final response = await _dioClient.post(
        '${ApiConstants.USERS}/avatar',
        data: formData,
      );
      return UserModel.fromJson(response.data as Map<String, dynamic>);
    } on DioException catch (e) {
      throw Exception(_handleError(e));
    }
  }

  String _handleError(DioException e) {
    if (e.response?.data != null && e.response?.data is Map) {
      final data = e.response?.data as Map<String, dynamic>;
      if (data['detail'] != null) return data['detail'] as String;
    }
    switch (e.response?.statusCode) {
      case 400:
        return 'Datos inválidos';
      case 401:
        return 'Sesión expirada';
      case 404:
        return 'Usuario no encontrado';
      case 500:
        return 'Error del servidor';
      default:
        return 'Sin conexión';
    }
  }
}
