import 'package:flutter_test/flutter_test.dart';

import 'package:espinargo_app/features/ratings/data/models/rating_model.dart';

void main() {
  group('RatingModel.fromJson', () {
    test('parsea todos los campos correctamente', () {
      final json = {
        'id': 'rat-1',
        'score': 5,
        'comment': 'Excelente servicio',
        'rating_type': 'passenger_to_driver',
        'created_at': '2024-01-01T00:00:00Z',
        'rater': {'id': 'u-1', 'full_name': 'Juan Quispe'},
      };

      final model = RatingModel.fromJson(json);

      expect(model.id, equals('rat-1'));
      expect(model.score, equals(5));
      expect(model.comment, equals('Excelente servicio'));
      expect(model.ratingType, equals('passenger_to_driver'));
      expect(model.createdAt, equals('2024-01-01T00:00:00Z'));
      expect(model.raterName, equals('Juan Quispe'));
    });

    test('comment nulo se parsea como null', () {
      final json = {
        'id': 'rat-2',
        'score': 4,
        'comment': null,
        'rating_type': 'driver_to_passenger',
        'created_at': '2024-01-01T00:00:00Z',
        'rater': {'id': 'u-2', 'full_name': 'Carlos Díaz'},
      };

      final model = RatingModel.fromJson(json);

      expect(model.comment, isNull);
      expect(model.score, equals(4));
    });

    test('rater nulo → raterName es null', () {
      final json = {
        'id': 'rat-3',
        'score': 3,
        'comment': null,
        'rating_type': 'passenger_to_driver',
        'created_at': '2024-01-01T00:00:00Z',
        'rater': null,
      };

      final model = RatingModel.fromJson(json);

      expect(model.raterName, isNull);
    });

    test('score 1 — límite inferior válido', () {
      final json = {
        'id': 'rat-4',
        'score': 1,
        'comment': null,
        'rating_type': 'passenger_to_driver',
        'created_at': '2024-01-01T00:00:00Z',
        'rater': null,
      };

      final model = RatingModel.fromJson(json);
      expect(model.score, equals(1));
    });

    test('rating_type ausente → cadena vacía por defecto', () {
      final json = {
        'id': 'rat-5',
        'score': 5,
        'comment': null,
        'created_at': '2024-01-01T00:00:00Z',
        'rater': null,
      };

      final model = RatingModel.fromJson(json);
      expect(model.ratingType, equals(''));
    });
  });
}
