import 'package:dio/dio.dart';
import 'package:flutter_secure_storage/flutter_secure_storage.dart';
import 'package:shared_preferences/shared_preferences.dart';

import '../../../../core/constants/api_constants.dart';
import '../../../../core/constants/storage_keys.dart';
import '../../../../core/network/dio_client.dart';
import '../models/user_model.dart';
import '../models/auth_response_model.dart';

/// Repositorio de autenticación.
/// Maneja todas las llamadas a la API de auth y el almacenamiento de tokens.
/// Es el único lugar que habla con la API de autenticación.
class AuthRepository {
  final DioClient _dioClient;
  final FlutterSecureStorage _secureStorage;

  AuthRepository({
    required DioClient dioClient,
    required FlutterSecureStorage secureStorage,
  })  : _dioClient = dioClient,
        _secureStorage = secureStorage;

  /// Registra un nuevo usuario.
  /// No guarda tokens, solo retorna el user_id para el siguiente paso (OTP).
  Future<RegisterResponseModel> register({
    required String fullName,
    required String phoneNumber,
    required String password,
    required String role,
    String? email,
  }) async {
    try {
      final response = await _dioClient.post(
        '${ApiConstants.AUTH}${ApiConstants.REGISTER}',
        data: {
          'full_name': fullName,
          'phone_number': phoneNumber,
          'password': password,
          'role': role,
          if (email != null) 'email': email,
        },
      );
      return RegisterResponseModel.fromJson(response.data as Map<String, dynamic>);
    } on DioException catch (e) {
      throw Exception(DioClient.parseError(e));
    }
  }

  /// Envia un código OTP al teléfono.
  Future<OTPResponseModel> sendOTP({
    required String phoneNumber,
    required String purpose,
  }) async {
    try {
      final response = await _dioClient.post(
        '${ApiConstants.AUTH}${ApiConstants.SEND_OTP}',
        data: {
          'phone_number': phoneNumber,
          'purpose': purpose,
        },
      );
      return OTPResponseModel.fromJson(response.data as Map<String, dynamic>);
    } on DioException catch (e) {
      throw Exception(DioClient.parseError(e));
    }
  }

  /// Verifica el código OTP.
  /// Retorna true si el código es válido.
  Future<bool> verifyPhone({
    required String phoneNumber,
    required String code,
    required String purpose,
  }) async {
    try {
      await _dioClient.post(
        '${ApiConstants.AUTH}${ApiConstants.VERIFY_PHONE}',
        data: {
          'phone_number': phoneNumber,
          'code': code,
          'purpose': purpose,
        },
      );
      return true;
    } on DioException catch (e) {
      throw Exception(DioClient.parseError(e));
    }
  }

  /// Inicia sesión con teléfono y contraseña.
  /// Guarda los tokens en storage seguro.
  Future<TokenResponseModel> login({
    required String phoneNumber,
    required String password,
    String? deviceName,
    String? deviceOs,
  }) async {
    try {
      final response = await _dioClient.post(
        '${ApiConstants.AUTH}${ApiConstants.LOGIN}',
        data: {
          'phone_number': phoneNumber,
          'password': password,
          if (deviceName != null) 'device_name': deviceName,
          if (deviceOs != null) 'device_os': deviceOs,
        },
      );

      final tokenResponse = TokenResponseModel.fromJson(response.data as Map<String, dynamic>);

      // Guardar tokens de forma segura
      await _secureStorage.write(
        key: StorageKeys.ACCESS_TOKEN,
        value: tokenResponse.accessToken,
      );
      await _secureStorage.write(
        key: StorageKeys.REFRESH_TOKEN,
        value: tokenResponse.refreshToken,
      );

      // Guardar datos básicos del usuario en SharedPreferences
      final prefs = await SharedPreferences.getInstance();
      await prefs.setString(StorageKeys.USER_ID, tokenResponse.user.id);
      await prefs.setString(StorageKeys.USER_NAME, tokenResponse.user.fullName);
      await prefs.setString(StorageKeys.USER_PHONE, tokenResponse.user.phoneNumber);
      await prefs.setString(StorageKeys.USER_ROLE, tokenResponse.user.role);
      if (tokenResponse.user.avatarUrl != null) {
        await prefs.setString(StorageKeys.USER_AVATAR, tokenResponse.user.avatarUrl!);
      }

      return tokenResponse;
    } on DioException catch (e) {
      throw Exception(DioClient.parseError(e));
    }
  }

  /// Cierra sesión del usuario.
  /// Siempre limpia el storage local aunque el server falle.
  Future<void> logout(String refreshToken) async {
    try {
      await _dioClient.post(
        '${ApiConstants.AUTH}${ApiConstants.LOGOUT}',
        data: {'refresh_token': refreshToken},
      );
    } catch (_) {
      // Continuar con la limpieza local aunque falle el server
    } finally {
      // Limpiar tokens del secure storage
      await _secureStorage.delete(key: StorageKeys.ACCESS_TOKEN);
      await _secureStorage.delete(key: StorageKeys.REFRESH_TOKEN);

      // Limpiar datos del usuario
      final prefs = await SharedPreferences.getInstance();
      await prefs.remove(StorageKeys.USER_ID);
      await prefs.remove(StorageKeys.USER_NAME);
      await prefs.remove(StorageKeys.USER_PHONE);
      await prefs.remove(StorageKeys.USER_ROLE);
      await prefs.remove(StorageKeys.USER_AVATAR);
    }
  }

  /// Obtiene el perfil del usuario logueado.
  Future<UserModel> getMyProfile() async {
    try {
      final response = await _dioClient.get(
        '${ApiConstants.AUTH}${ApiConstants.ME}',
      );
      return UserModel.fromJson(response.data as Map<String, dynamic>);
    } on DioException catch (e) {
      throw Exception(DioClient.parseError(e));
    }
  }

  /// Solicita recuperación de contraseña.
  Future<MessageResponseModel> forgotPassword(String phone) async {
    try {
      final response = await _dioClient.post(
        '${ApiConstants.AUTH}${ApiConstants.FORGOT_PASSWORD}',
        data: {'phone_number': phone},
      );
      return MessageResponseModel.fromJson(response.data as Map<String, dynamic>);
    } on DioException catch (e) {
      throw Exception(DioClient.parseError(e));
    }
  }

  /// Restablece la contraseña con el código OTP verificado.
  Future<MessageResponseModel> resetPassword({
    required String phoneNumber,
    required String otpCode,
    required String newPassword,
  }) async {
    try {
      final response = await _dioClient.post(
        '${ApiConstants.AUTH}${ApiConstants.RESET_PASSWORD}',
        data: {
          'phone_number': phoneNumber,
          'otp_code': otpCode,
          'new_password': newPassword,
        },
      );
      return MessageResponseModel.fromJson(response.data as Map<String, dynamic>);
    } on DioException catch (e) {
      throw Exception(DioClient.parseError(e));
    }
  }

  /// Obtiene los tokens guardados en el storage seguro.
  /// Retorna un mapa con access_token y refresh_token.
  Future<Map<String, String?>> getSavedTokens() async {
    final accessToken = await _secureStorage.read(key: StorageKeys.ACCESS_TOKEN);
    final refreshToken = await _secureStorage.read(key: StorageKeys.REFRESH_TOKEN);
    return {
      'access_token': accessToken,
      'refresh_token': refreshToken,
    };
  }

  /// Registra el token FCM del dispositivo en el backend.
  /// Falla silenciosamente para no interrumpir el flujo de login.
  Future<void> updateDeviceToken(String token) async {
    try {
      await _dioClient.patch(
        ApiConstants.DEVICE_TOKEN,
        data: {'device_token': token},
      );
    } catch (_) {}
  }
}