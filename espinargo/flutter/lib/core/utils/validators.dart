import '../constants/app_constants.dart';

/// Funciones de validación para formularios Flutter.
/// Compatible con el parámetro validator de TextFormField.
class Validators {
  /// Valida número de celular peruano.
  /// Ejemplos válidos: 987654321, +51987654321
  static String? phone(String? value) {
    if (value == null || value.isEmpty) {
      return 'Ingresa tu número de celular';
    }
    
    final cleaned = value.replaceAll(RegExp(r'[\s\-()]'), '');
    final regex = RegExp(r'^(\+51)?9[0-9]{8}$');
    
    if (!regex.hasMatch(cleaned)) {
      return 'Ingresa un celular peruano válido (ej: 987654321)';
    }
    
    return null;
  }

  /// Valida contraseña.
  static String? password(String? value) {
    if (value == null || value.isEmpty) {
      return 'Ingresa tu contraseña';
    }
    if (value.length < 6) {
      return 'Mínimo 6 caracteres';
    }
    if (value.length > 128) {
      return 'Contraseña demasiado larga';
    }
    return null;
  }

  /// Valida campo obligatorio genérico.
  static String? requiredField(String? value, String fieldName) {
    if (value == null || value.isEmpty) {
      return 'Ingresa $fieldName';
    }
    return null;
  }

  /// Valida nombre.
  static String? name(String? value) {
    if (value == null || value.isEmpty) {
      return 'Ingresa tu nombre';
    }
    if (value.length < 2) {
      return 'El nombre es muy corto';
    }
    if (value.length > 150) {
      return 'El nombre es demasiado largo';
    }
    return null;
  }

  /// Valida precio.
  static String? price(String? value) {
    if (value == null || value.isEmpty) {
      return 'Ingresa el precio';
    }
    
    final parsed = double.tryParse(value);
    if (parsed == null) {
      return 'Ingresa un precio válido (ej: 5.50)';
    }
    if (parsed <= 0) {
      return 'El precio debe ser mayor a cero';
    }
    if (parsed > AppConstants.MAX_TRIP_PRICE) {
      return 'El precio máximo es S/999';
    }
    return null;
  }

  /// Valida código OTP.
  static String? otpCode(String? value) {
    if (value == null || value.isEmpty) {
      return 'Ingresa el código';
    }
    if (value.length != 6) {
      return 'El código debe tener 6 dígitos';
    }
    if (!RegExp(r'^[0-9]+$').hasMatch(value)) {
      return 'Solo números';
    }
    return null;
  }

  /// Valida email (opcional).
  static String? email(String? value) {
    if (value == null || value.isEmpty) {
      return null; // Email es opcional
    }
    
    final regex = RegExp(r'^[\w-\.]+@([\w-]+\.)+[\w-]{2,4}$');
    if (!regex.hasMatch(value)) {
      return 'Ingresa un correo válido';
    }
    return null;
  }
}