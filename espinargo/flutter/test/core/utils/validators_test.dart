import 'package:flutter_test/flutter_test.dart';
import 'package:espinargo_app/core/utils/validators.dart';

void main() {
  group('Validators.phone', () {
    test('retorna null para número válido sin prefijo', () {
      expect(Validators.phone('987654321'), isNull);
    });

    test('retorna null para número válido con prefijo +51', () {
      expect(Validators.phone('+51987654321'), isNull);
    });

    test('retorna error para campo vacío', () {
      expect(Validators.phone(''), isNotNull);
      expect(Validators.phone(null), isNotNull);
    });

    test('retorna error para número que no empieza en 9', () {
      expect(Validators.phone('187654321'), isNotNull);
    });

    test('retorna error para número de menos de 9 dígitos', () {
      expect(Validators.phone('9876543'), isNotNull);
    });

    test('retorna error para número de más de 9 dígitos', () {
      expect(Validators.phone('9876543210'), isNotNull);
    });

    test('acepta número con espacios (los limpia internamente)', () {
      expect(Validators.phone('987 654 321'), isNull);
    });
  });

  group('Validators.password', () {
    test('retorna null para contraseña válida', () {
      expect(Validators.password('secreto'), isNull);
    });

    test('retorna error para campo vacío', () {
      expect(Validators.password(''), isNotNull);
      expect(Validators.password(null), isNotNull);
    });

    test('retorna error para contraseña de menos de 6 caracteres', () {
      expect(Validators.password('abc'), isNotNull);
    });

    test('retorna null para exactamente 6 caracteres', () {
      expect(Validators.password('abcdef'), isNull);
    });

    test('retorna error para contraseña de más de 128 caracteres', () {
      expect(Validators.password('a' * 129), isNotNull);
    });

    test('retorna null para exactamente 128 caracteres', () {
      expect(Validators.password('a' * 128), isNull);
    });
  });

  group('Validators.name', () {
    test('retorna null para nombre válido', () {
      expect(Validators.name('Juan'), isNull);
    });

    test('retorna error para campo vacío', () {
      expect(Validators.name(''), isNotNull);
      expect(Validators.name(null), isNotNull);
    });

    test('retorna error para nombre de 1 caracter', () {
      expect(Validators.name('J'), isNotNull);
    });

    test('retorna null para exactamente 2 caracteres', () {
      expect(Validators.name('Jo'), isNull);
    });

    test('retorna error para nombre de más de 150 caracteres', () {
      expect(Validators.name('A' * 151), isNotNull);
    });
  });

  group('Validators.price', () {
    test('retorna null para precio válido', () {
      expect(Validators.price('5.50'), isNull);
    });

    test('retorna null para precio entero', () {
      expect(Validators.price('10'), isNull);
    });

    test('retorna error para campo vacío', () {
      expect(Validators.price(''), isNotNull);
      expect(Validators.price(null), isNotNull);
    });

    test('retorna error para texto no numérico', () {
      expect(Validators.price('abc'), isNotNull);
    });

    test('retorna error para precio cero', () {
      expect(Validators.price('0'), isNotNull);
    });

    test('retorna error para precio negativo', () {
      expect(Validators.price('-5'), isNotNull);
    });

    test('retorna error para precio mayor al máximo (999)', () {
      expect(Validators.price('1000'), isNotNull);
    });

    test('retorna null para el precio máximo exacto', () {
      expect(Validators.price('999'), isNull);
    });
  });

  group('Validators.otpCode', () {
    test('retorna null para código válido de 6 dígitos', () {
      expect(Validators.otpCode('123456'), isNull);
    });

    test('retorna error para campo vacío', () {
      expect(Validators.otpCode(''), isNotNull);
      expect(Validators.otpCode(null), isNotNull);
    });

    test('retorna error para código de menos de 6 dígitos', () {
      expect(Validators.otpCode('12345'), isNotNull);
    });

    test('retorna error para código de más de 6 dígitos', () {
      expect(Validators.otpCode('1234567'), isNotNull);
    });

    test('retorna error para código con letras', () {
      expect(Validators.otpCode('12345a'), isNotNull);
    });
  });

  group('Validators.email', () {
    test('retorna null para email vacío (campo opcional)', () {
      expect(Validators.email(''), isNull);
      expect(Validators.email(null), isNull);
    });

    test('retorna null para email válido', () {
      expect(Validators.email('usuario@ejemplo.com'), isNull);
    });

    test('retorna error para email sin @', () {
      expect(Validators.email('usuarioejemplo.com'), isNotNull);
    });

    test('retorna error para email sin dominio', () {
      expect(Validators.email('usuario@'), isNotNull);
    });
  });

  group('Validators.requiredField', () {
    test('retorna null para campo con valor', () {
      expect(Validators.requiredField('algo', 'el campo'), isNull);
    });

    test('retorna error para campo vacío', () {
      expect(Validators.requiredField('', 'el campo'), isNotNull);
      expect(Validators.requiredField(null, 'el campo'), isNotNull);
    });
  });
}
