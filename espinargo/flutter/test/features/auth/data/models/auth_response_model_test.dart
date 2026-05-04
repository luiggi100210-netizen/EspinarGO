import 'package:flutter_test/flutter_test.dart';
import 'package:espinargo_app/features/auth/data/models/auth_response_model.dart';

final _userJson = {
  'id': 'u-1',
  'full_name': 'Ana Flores',
  'phone_number': '+51912345678',
  'email': null,
  'role': 'passenger',
  'status': 'active',
  'phone_verified': true,
  'avatar_url': null,
  'preferred_lang': 'es',
  'created_at': '2024-01-01T00:00:00Z',
};

void main() {
  group('TokenResponseModel.fromJson', () {
    test('parsea todos los campos', () {
      final json = {
        'access_token': 'access_abc',
        'refresh_token': 'refresh_xyz',
        'token_type': 'Bearer',
        'expires_in': 1800,
        'user': _userJson,
      };
      final model = TokenResponseModel.fromJson(json);
      expect(model.accessToken, equals('access_abc'));
      expect(model.refreshToken, equals('refresh_xyz'));
      expect(model.tokenType, equals('Bearer'));
      expect(model.expiresIn, equals(1800));
      expect(model.user.fullName, equals('Ana Flores'));
    });

    test('usa valores por defecto para campos opcionales', () {
      final json = {
        'access_token': 'access_abc',
        'refresh_token': 'refresh_xyz',
        'user': _userJson,
      };
      final model = TokenResponseModel.fromJson(json);
      expect(model.tokenType, equals('Bearer'));
      expect(model.expiresIn, equals(1800));
    });

    test('toJson serializa correctamente', () {
      final json = {
        'access_token': 'tok',
        'refresh_token': 'ref',
        'token_type': 'Bearer',
        'expires_in': 900,
        'user': _userJson,
      };
      final model = TokenResponseModel.fromJson(json);
      final out = model.toJson();
      expect(out['access_token'], equals('tok'));
      expect(out['refresh_token'], equals('ref'));
    });
  });

  group('OTPResponseModel.fromJson', () {
    test('parsea todos los campos', () {
      final json = {
        'message': 'OTP enviado',
        'expires_in': 60,
        'masked_phone': '***4321',
      };
      final model = OTPResponseModel.fromJson(json);
      expect(model.message, equals('OTP enviado'));
      expect(model.expiresIn, equals(60));
      expect(model.maskedPhone, equals('***4321'));
    });

    test('usa valores por defecto para campos opcionales', () {
      final model = OTPResponseModel.fromJson({});
      expect(model.expiresIn, equals(60));
      expect(model.message, equals(''));
      expect(model.maskedPhone, equals(''));
    });
  });

  group('RegisterResponseModel.fromJson', () {
    test('parsea todos los campos', () {
      final json = {
        'message': 'Registro exitoso',
        'user_id': 'u-999',
        'phone_number': '+51987654321',
        'next_step': 'otp_verification',
      };
      final model = RegisterResponseModel.fromJson(json);
      expect(model.message, equals('Registro exitoso'));
      expect(model.userId, equals('u-999'));
      expect(model.phoneNumber, equals('+51987654321'));
      expect(model.nextStep, equals('otp_verification'));
    });

    test('usa valor por defecto para next_step', () {
      final model = RegisterResponseModel.fromJson({'user_id': 'u-1'});
      expect(model.nextStep, equals('otp_verification'));
    });
  });

  group('MessageResponseModel.fromJson', () {
    test('parsea mensaje y success', () {
      final json = {'message': 'OK', 'success': true};
      final model = MessageResponseModel.fromJson(json);
      expect(model.message, equals('OK'));
      expect(model.success, isTrue);
    });

    test('success es true por defecto', () {
      final model = MessageResponseModel.fromJson({'message': 'ok'});
      expect(model.success, isTrue);
    });
  });
}
