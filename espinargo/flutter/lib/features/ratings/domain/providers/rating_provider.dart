import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../../../core/providers.dart';
import '../../data/repositories/rating_repository.dart';

/// Provider del repositorio de calificaciones.
final ratingRepositoryProvider = Provider<RatingRepository>((ref) {
  return RatingRepository(dioClient: ref.watch(dioClientProvider));
});
