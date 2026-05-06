import 'package:flutter_test/flutter_test.dart';

import 'package:espinargo_app/features/packages/data/models/package_model.dart';

void main() {
  // ── Fixtures ────────────────────────────────────────────────────────────────

  Map<String, dynamic> _fullJson() => {
        'id': 'pkg-1',
        'tracking_code': 'ESP-001234',
        'sender': null,
        'driver': null,
        'recipient_name': 'María López',
        'recipient_phone': '+51987654321',
        'delivery_address': 'Jr. Junín 123, Espinar',
        'delivery_lat': '-14.832',
        'delivery_lng': '-71.013',
        'size': 'small',
        'description': 'Ropa y documentos',
        'is_fragile': true,
        'photo_url': 'https://cdn.example.com/photo.jpg',
        'status': 'pending',
        'price': '5.50',
        'payment_method': 'cash',
        'created_at': '2024-01-01T00:00:00Z',
        'picked_up_at': null,
        'delivered_at': null,
      };

  // ── fromJson ───────────────────────────────────────────────────────────────

  group('PackageModel.fromJson', () {
    test('parsea todos los campos correctamente', () {
      final model = PackageModel.fromJson(_fullJson());

      expect(model.id, equals('pkg-1'));
      expect(model.trackingCode, equals('ESP-001234'));
      expect(model.recipientName, equals('María López'));
      expect(model.recipientPhone, equals('+51987654321'));
      expect(model.deliveryAddress, equals('Jr. Junín 123, Espinar'));
      expect(model.deliveryLat, equals('-14.832'));
      expect(model.deliveryLng, equals('-71.013'));
      expect(model.size, equals('small'));
      expect(model.description, equals('Ropa y documentos'));
      expect(model.isFragile, isTrue);
      expect(model.photoUrl, equals('https://cdn.example.com/photo.jpg'));
      expect(model.status, equals('pending'));
      expect(model.price, equals('5.50'));
      expect(model.paymentMethod, equals('cash'));
      expect(model.createdAt, equals('2024-01-01T00:00:00Z'));
    });

    test('campos opcionales nulos se parsean como null', () {
      final json = {
        ..._fullJson(),
        'delivery_lat': null,
        'delivery_lng': null,
        'photo_url': null,
        'price': null,
        'picked_up_at': null,
        'delivered_at': null,
      };
      final model = PackageModel.fromJson(json);

      expect(model.deliveryLat, isNull);
      expect(model.deliveryLng, isNull);
      expect(model.photoUrl, isNull);
      expect(model.price, isNull);
      expect(model.pickedUpAt, isNull);
      expect(model.deliveredAt, isNull);
    });

    test('is_fragile ausente → false por defecto', () {
      final json = Map<String, dynamic>.from(_fullJson())..remove('is_fragile');
      final model = PackageModel.fromJson(json);
      expect(model.isFragile, isFalse);
    });

    test('size ausente → medium por defecto', () {
      final json = Map<String, dynamic>.from(_fullJson())..remove('size');
      final model = PackageModel.fromJson(json);
      expect(model.size, equals('medium'));
    });

    test('status ausente → pending por defecto', () {
      final json = Map<String, dynamic>.from(_fullJson())..remove('status');
      final model = PackageModel.fromJson(json);
      expect(model.status, equals('pending'));
    });

    test('payment_method ausente → cash por defecto', () {
      final json = Map<String, dynamic>.from(_fullJson())..remove('payment_method');
      final model = PackageModel.fromJson(json);
      expect(model.paymentMethod, equals('cash'));
    });
  });

  // ── computed getters ───────────────────────────────────────────────────────

  group('isActive / isDelivered / isCancelled', () {
    for (final status in ['pending', 'assigned', 'picked_up', 'in_transit']) {
      test('status $status → isActive = true', () {
        final model = PackageModel.fromJson({..._fullJson(), 'status': status});
        expect(model.isActive, isTrue);
        expect(model.isDelivered, isFalse);
        expect(model.isCancelled, isFalse);
      });
    }

    test('status delivered → isDelivered = true', () {
      final model = PackageModel.fromJson({..._fullJson(), 'status': 'delivered'});
      expect(model.isDelivered, isTrue);
      expect(model.isActive, isFalse);
    });

    test('status cancelled → isCancelled = true', () {
      final model = PackageModel.fromJson({..._fullJson(), 'status': 'cancelled'});
      expect(model.isCancelled, isTrue);
      expect(model.isActive, isFalse);
    });
  });

  group('sizeLabel', () {
    test('envelope → Sobre / Documento', () {
      final model = PackageModel.fromJson({..._fullJson(), 'size': 'envelope'});
      expect(model.sizeLabel, equals('Sobre / Documento'));
    });

    test('small → Paquete pequeño', () {
      final model = PackageModel.fromJson({..._fullJson(), 'size': 'small'});
      expect(model.sizeLabel, equals('Paquete pequeño'));
    });

    test('large → Paquete grande', () {
      final model = PackageModel.fromJson({..._fullJson(), 'size': 'large'});
      expect(model.sizeLabel, equals('Paquete grande'));
    });

    test('desconocido → Paquete', () {
      final model = PackageModel.fromJson({..._fullJson(), 'size': 'unknown'});
      expect(model.sizeLabel, equals('Paquete'));
    });
  });

  // ── copyWith ───────────────────────────────────────────────────────────────

  group('copyWith', () {
    test('actualiza solo los campos indicados', () {
      final original = PackageModel.fromJson(_fullJson());
      final copy = original.copyWith(status: 'delivered', price: '10.00');

      expect(copy.status, equals('delivered'));
      expect(copy.price, equals('10.00'));
      expect(copy.id, equals(original.id));
      expect(copy.recipientName, equals(original.recipientName));
    });

    test('sin argumentos devuelve copia idéntica', () {
      final original = PackageModel.fromJson(_fullJson());
      final copy = original.copyWith();

      expect(copy.id, equals(original.id));
      expect(copy.status, equals(original.status));
    });
  });
}
