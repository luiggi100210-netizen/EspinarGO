/// Modelo de datos del usuario.
///
/// Representa los campos que retorna la API de autenticación.
/// Los nombres del JSON usan snake_case (ej: phone_number),
/// el modelo Dart usa camelCase (ej: phoneNumber).
class UserModel {
  final String id;
  final String fullName;
  final String phoneNumber;
  final String? email;
  final String role;
  final String status;
  final bool phoneVerified;
  final String? avatarUrl;
  final String preferredLang;
  final String createdAt;

  const UserModel({
    required this.id,
    required this.fullName,
    required this.phoneNumber,
    this.email,
    required this.role,
    required this.status,
    required this.phoneVerified,
    this.avatarUrl,
    required this.preferredLang,
    required this.createdAt,
  });

  /// Crea un UserModel desde un JSON de la API.
  /// Los campos del JSON usan snake_case.
  factory UserModel.fromJson(Map<String, dynamic> json) {
    return UserModel(
      id: json['id'] as String,
      fullName: json['full_name'] as String,
      phoneNumber: json['phone_number'] as String,
      email: json['email'] as String?,
      role: json['role'] as String,
      status: json['status'] as String,
      phoneVerified: json['phone_verified'] as bool? ?? false,
      avatarUrl: json['avatar_url'] as String?,
      preferredLang: json['preferred_lang'] ?? 'es',
      createdAt: json['created_at'] as String,
    );
  }

  /// Convierte el modelo a JSON para enviar a la API.
  Map<String, dynamic> toJson() {
    return {
      'id': id,
      'full_name': fullName,
      'phone_number': phoneNumber,
      'email': email,
      'role': role,
      'status': status,
      'phone_verified': phoneVerified,
      'avatar_url': avatarUrl,
      'preferred_lang': preferredLang,
      'created_at': createdAt,
    };
  }

  /// Crea una copia del usuario con campos actualizados.
  UserModel copyWith({
    String? id,
    String? fullName,
    String? phoneNumber,
    String? email,
    String? role,
    String? status,
    bool? phoneVerified,
    String? avatarUrl,
    String? preferredLang,
    String? createdAt,
  }) {
    return UserModel(
      id: id ?? this.id,
      fullName: fullName ?? this.fullName,
      phoneNumber: phoneNumber ?? this.phoneNumber,
      email: email ?? this.email,
      role: role ?? this.role,
      status: status ?? this.status,
      phoneVerified: phoneVerified ?? this.phoneVerified,
      avatarUrl: avatarUrl ?? this.avatarUrl,
      preferredLang: preferredLang ?? this.preferredLang,
      createdAt: createdAt ?? this.createdAt,
    );
  }

  /// Retorna true si el usuario es pasajero.
  bool get isPassenger => role == 'passenger';

  /// Retorna true si el usuario es conductor.
  bool get isDriver => role == 'driver';

  /// Retorna true si el usuario es administrador.
  bool get isAdmin => role == 'admin';

  /// Retorna true si el usuario está activo.
  bool get isActive => status == 'active';

  /// Retorna las iniciales del nombre.
  /// Ejemplo: "Juan Quispe" → "JQ"
  String get initials {
    final parts = fullName.trim().split(' ');
    if (parts.length < 2) return parts.first.substring(0, 1).toUpperCase();
    return '${parts.first[0]}${parts[1][0]}'.toUpperCase();
  }

  @override
  String toString() {
    return 'UserModel(id: $id, fullName: $fullName, phoneNumber: $phoneNumber, role: $role, status: $status)';
  }
}