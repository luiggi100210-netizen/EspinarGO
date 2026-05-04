import 'package:flutter_test/flutter_test.dart';
import 'package:intl/date_symbol_data_local.dart';
import 'package:espinargo_app/core/utils/formatters.dart';

void main() {
  setUpAll(() async {
    await initializeDateFormatting('es');
  });

  group('Formatters.currency', () {
    test('formatea entero con dos decimales', () {
      expect(Formatters.currency(5), contains('5.00'));
      expect(Formatters.currency(5), contains('S/'));
    });

    test('formatea decimal correctamente', () {
      expect(Formatters.currency(12.5), contains('12.50'));
    });

    test('formatea cero', () {
      expect(Formatters.currency(0), contains('0.00'));
    });
  });

  group('Formatters.currencyFromString', () {
    test('convierte string numérico a moneda', () {
      expect(Formatters.currencyFromString('5.50'), contains('5.50'));
    });

    test('retorna cero para string inválido', () {
      expect(Formatters.currencyFromString('abc'), contains('0.00'));
    });
  });

  group('Formatters.distance', () {
    test('formatea distancia menor a 1 km en metros', () {
      expect(Formatters.distance(0.5), equals('500 m'));
      expect(Formatters.distance(0.85), equals('850 m'));
    });

    test('formatea distancia mayor o igual a 1 km en kilómetros', () {
      expect(Formatters.distance(1.0), equals('1.0 km'));
      expect(Formatters.distance(2.5), equals('2.5 km'));
    });
  });

  group('Formatters.duration', () {
    test('formatea minutos menores a 60', () {
      expect(Formatters.duration(5), equals('5 min'));
      expect(Formatters.duration(45), equals('45 min'));
    });

    test('formatea exactamente 60 minutos como 1 hora', () {
      expect(Formatters.duration(60), equals('1 h'));
    });

    test('formatea horas y minutos', () {
      expect(Formatters.duration(90), equals('1 h 30 min'));
    });

    test('formatea múltiples horas sin minutos', () {
      expect(Formatters.duration(120), equals('2 h'));
    });
  });

  group('Formatters.maskedPhone', () {
    test('enmascara dejando solo los últimos 4 dígitos', () {
      expect(Formatters.maskedPhone('+51987654321'), equals('+51 ****** 4321'));
    });

    test('retorna el número original si tiene menos de 4 caracteres', () {
      expect(Formatters.maskedPhone('123'), equals('123'));
    });
  });

  group('Formatters.initials', () {
    test('extrae iniciales de nombre y apellido', () {
      expect(Formatters.initials('Juan Quispe'), equals('JQ'));
    });

    test('retorna primera inicial para nombre sin apellido', () {
      expect(Formatters.initials('Juan'), equals('J'));
    });

    test('usa mayúsculas', () {
      expect(Formatters.initials('ana flores'), equals('AF'));
    });
  });

  group('Formatters.vehicleType', () {
    test('traduce mototaxi', () {
      expect(Formatters.vehicleType('mototaxi'), equals('Mototaxi'));
    });

    test('traduce car', () {
      expect(Formatters.vehicleType('car'), equals('Auto'));
    });

    test('retorna el valor original para tipo desconocido', () {
      expect(Formatters.vehicleType('bus'), equals('bus'));
    });
  });

  group('Formatters.tripStatus', () {
    final cases = {
      'searching': 'Buscando conductor',
      'negotiating': 'Revisando ofertas',
      'accepted': 'Conductor en camino',
      'in_progress': 'En curso',
      'completed': 'Completado',
      'cancelled': 'Cancelado',
    };

    cases.forEach((input, expected) {
      test('traduce estado $input', () {
        expect(Formatters.tripStatus(input), equals(expected));
      });
    });

    test('retorna el valor original para estado desconocido', () {
      expect(Formatters.tripStatus('unknown'), equals('unknown'));
    });
  });

  group('Formatters.packageStatus', () {
    test('traduce pending', () {
      expect(Formatters.packageStatus('pending'), equals('Esperando conductor'));
    });

    test('traduce delivered', () {
      expect(Formatters.packageStatus('delivered'), equals('Entregado'));
    });

    test('retorna el valor original para estado desconocido', () {
      expect(Formatters.packageStatus('xyz'), equals('xyz'));
    });
  });

  group('Formatters.driverStatus', () {
    test('traduce approved', () {
      expect(Formatters.driverStatus('approved'), equals('Aprobado'));
    });

    test('traduce rejected', () {
      expect(Formatters.driverStatus('rejected'), equals('Rechazado'));
    });

    test('retorna el valor original para estado desconocido', () {
      expect(Formatters.driverStatus('xyz'), equals('xyz'));
    });
  });

  group('Formatters.timeAgo', () {
    test('retorna "hace un momento" para diferencia de segundos', () {
      final date = DateTime.now().subtract(const Duration(seconds: 30));
      expect(Formatters.timeAgo(date), equals('hace un momento'));
    });

    test('retorna minutos en singular', () {
      final date = DateTime.now().subtract(const Duration(minutes: 1));
      expect(Formatters.timeAgo(date), equals('hace 1 minuto'));
    });

    test('retorna minutos en plural', () {
      final date = DateTime.now().subtract(const Duration(minutes: 5));
      expect(Formatters.timeAgo(date), equals('hace 5 minutos'));
    });

    test('retorna horas', () {
      final date = DateTime.now().subtract(const Duration(hours: 2));
      expect(Formatters.timeAgo(date), equals('hace 2 horas'));
    });

    test('retorna días', () {
      final date = DateTime.now().subtract(const Duration(days: 3));
      expect(Formatters.timeAgo(date), equals('hace 3 días'));
    });
  });
}
