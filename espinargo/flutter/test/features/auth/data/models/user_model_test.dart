import 'package:flutter_test/flutter_test.dart';
import 'package:espinargo_app/features/auth/data/models/user_model.dart';

Map<String, dynamic> _userJson({String role = 'passenger'}) => {
      'id': 'user-123',
      'full_name': 'Juan Quispe',
      'phone_number': '+51987654321',
      'email': 'juan@example.com',
      'role': role,
      'status': 'active',
      'phone_verified': true,
      'avatar_url': null,
      'preferred_lang': 'es',
      'created_at': '2024-01-20T10:00:00Z',
    };

void main() {
  group('UserModel.fromJson', () {
    test('parsea todos los campos correctamente', () {
      final user = UserModel.fromJson(_userJson());
      expect(user.id, equals('user-123'));
      expect(user.fullName, equals('Juan Quispe'));
      expect(user.phoneNumber, equals('+51987654321'));
      expect(user.email, equals('juan@example.com'));
      expect(user.role, equals('passenger'));
      expect(user.status, equals('active'));
      expect(user.phoneVerified, isTrue);
      expect(user.avatarUrl, isNull);
      expect(user.preferredLang, equals('es'));
    });

    test('usa "es" como preferredLang por defecto si no viene en JSON', () {
      final json = _userJson()..remove('preferred_lang');
      final user = UserModel.fromJson(json);
      expect(user.preferredLang, equals('es'));
    });

    test('phoneVerified es false por defecto si no viene en JSON', () {
      final json = _userJson()..remove('phone_verified');
      final user = UserModel.fromJson(json);
      expect(user.phoneVerified, isFalse);
    });
  });

  group('UserModel.toJson', () {
    test('serializa todos los campos correctamente', () {
      final user = UserModel.fromJson(_userJson());
      final json = user.toJson();
      expect(json['id'], equals('user-123'));
      expect(json['full_name'], equals('Juan Quispe'));
      expect(json['phone_number'], equals('+51987654321'));
      expect(json['role'], equals('passenger'));
    });
  });

  group('UserModel.copyWith', () {
    test('actualiza solo los campos indicados', () {
      final user = UserModel.fromJson(_userJson());
      final updated = user.copyWith(fullName: 'Pedro Mamani');
      expect(updated.fullName, equals('Pedro Mamani'));
      expect(updated.id, equals(user.id));
      expect(updated.role, equals(user.role));
    });
  });

  group('UserModel getters de rol', () {
    test('isPassenger es true para rol passenger', () {
      final user = UserModel.fromJson(_userJson(role: 'passenger'));
      expect(user.isPassenger, isTrue);
      expect(user.isDriver, isFalse);
      expect(user.isAdmin, isFalse);
    });

    test('isDriver es true para rol driver', () {
      final user = UserModel.fromJson(_userJson(role: 'driver'));
      expect(user.isDriver, isTrue);
      expect(user.isPassenger, isFalse);
    });

    test('isAdmin es true para rol admin', () {
      final user = UserModel.fromJson(_userJson(role: 'admin'));
      expect(user.isAdmin, isTrue);
    });
  });

  group('UserModel.isActive', () {
    test('retorna true para status active', () {
      final user = UserModel.fromJson(_userJson());
      expect(user.isActive, isTrue);
    });

    test('retorna false para status distinto a active', () {
      final user = UserModel.fromJson({..._userJson(), 'status': 'suspended'});
      expect(user.isActive, isFalse);
    });
  });

  group('UserModel.initials', () {
    test('retorna iniciales de nombre y apellido', () {
      final user = UserModel.fromJson(_userJson());
      expect(user.initials, equals('JQ'));
    });

    test('retorna primera inicial para nombre sin apellido', () {
      final user = UserModel.fromJson({..._userJson(), 'full_name': 'Juan'});
      expect(user.initials, equals('J'));
    });
  });
}
