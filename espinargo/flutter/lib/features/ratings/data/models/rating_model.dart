/// Modelo de calificación de un viaje.
class RatingModel {
  final String id;
  final int score;
  final String? comment;
  final String ratingType;
  final String createdAt;
  final String? raterName;

  const RatingModel({
    required this.id,
    required this.score,
    this.comment,
    required this.ratingType,
    required this.createdAt,
    this.raterName,
  });

  factory RatingModel.fromJson(Map<String, dynamic> json) {
    final rater = json['rater'] as Map<String, dynamic>?;
    return RatingModel(
      id: json['id'] as String,
      score: json['score'] as int,
      comment: json['comment'] as String?,
      ratingType: json['rating_type'] as String? ?? '',
      createdAt: json['created_at'] as String? ?? '',
      raterName: rater?['full_name'] as String?,
    );
  }
}
