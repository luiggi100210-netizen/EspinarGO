import 'user_model.dart';

/// Respuesta del API al hacer login.
/// Incluye tokens y datos del usuario.
class TokenResponseModel {
  final String accessToken;
  final String refreshToken;
  final String tokenType;
  final int expiresIn;
  final UserModel user;

  const TokenResponseModel({
    required this.accessToken,
    required this.refreshToken,
    required this.tokenType,
    required this.expiresIn,
    required this.user,
  });

  /// Crea desde el JSON de la respuesta del login.
  factory TokenResponseModel.fromJson(Map<String, dynamic> json) {
    return TokenResponseModel(
      accessToken: json['access_token'] as String,
      refreshToken: json['refresh_token'] as String,
      tokenType: json['token_type'] as String? ?? 'Bearer',
      expiresIn: json['expires_in'] as int? ?? 1800,
      user: UserModel.fromJson(json['user'] as Map<String, dynamic>),
    );
  }

  Map<String, dynamic> toJson() {
    return {
      'access_token': accessToken,
      'refresh_token': refreshToken,
      'token_type': tokenType,
      'expires_in': expiresIn,
      'user': user.toJson(),
    };
  }
}

/// Respuesta del API al enviar OTP.
class OTPResponseModel {
  final String message;
  final int expiresIn;
  final String maskedPhone;

  const OTPResponseModel({
    required this.message,
    required this.expiresIn,
    required this.maskedPhone,
  });

  factory OTPResponseModel.fromJson(Map<String, dynamic> json) {
    return OTPResponseModel(
      message: json['message'] as String? ?? '',
      expiresIn: json['expires_in'] as int? ?? 60,
      maskedPhone: json['masked_phone'] as String? ?? '',
    );
  }

  Map<String, dynamic> toJson() {
    return {
      'message': message,
      'expires_in': expiresIn,
      'masked_phone': maskedPhone,
    };
  }
}

/// Respuesta del API al registrar un nuevo usuario.
class RegisterResponseModel {
  final String message;
  final String userId;
  final String phoneNumber;
  final String nextStep;

  const RegisterResponseModel({
    required this.message,
    required this.userId,
    required this.phoneNumber,
    required this.nextStep,
  });

  factory RegisterResponseModel.fromJson(Map<String, dynamic> json) {
    return RegisterResponseModel(
      message: json['message'] as String? ?? '',
      userId: json['user_id'] as String? ?? '',
      phoneNumber: json['phone_number'] as String? ?? '',
      nextStep: json['next_step'] as String? ?? 'otp_verification',
    );
  }

  Map<String, dynamic> toJson() {
    return {
      'message': message,
      'user_id': userId,
      'phone_number': phoneNumber,
      'next_step': nextStep,
    };
  }
}

/// Respuesta genérica del API con solo un mensaje.
class MessageResponseModel {
  final String message;
  final bool success;

  const MessageResponseModel({
    required this.message,
    required this.success,
  });

  factory MessageResponseModel.fromJson(Map<String, dynamic> json) {
    return MessageResponseModel(
      message: json['message'] as String? ?? '',
      success: json['success'] as bool? ?? true,
    );
  }

  Map<String, dynamic> toJson() {
    return {
      'message': message,
      'success': success,
    };
  }
}