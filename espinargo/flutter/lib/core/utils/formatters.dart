import 'package:intl/intl.dart';

/// Funciones para formatear datos para mostrar en la UI.
class Formatters {
  /// Formatea precio en soles: "S/ 5.00"
  static String currency(double amount) {
    final format = NumberFormat.currency(symbol: 'S/ ', decimalDigits: 2);
    return format.format(amount);
  }

  /// Formatea precio desde string.
  static String currencyFromString(String amount) {
    final parsed = double.tryParse(amount) ?? 0.0;
    return currency(parsed);
  }

  /// Formatea fecha: "20 ene 2024"
  static String date(DateTime date) {
    return DateFormat('dd MMM yyyy', 'es').format(date);
  }

  /// Formatea fecha y hora: "20 ene 2024, 14:35"
  static String dateTime(DateTime date) {
    return DateFormat('dd MMM yyyy, HH:mm', 'es').format(date);
  }

  /// Formatea tiempo relativo: "hace 5 minutos", "hace 2 horas"
  static String timeAgo(DateTime date) {
    final now = DateTime.now();
    final diff = now.difference(date);

    if (diff.inSeconds < 60) return 'hace un momento';
    if (diff.inMinutes < 60) return 'hace ${diff.inMinutes} minuto${diff.inMinutes > 1 ? 's' : ''}';
    if (diff.inHours < 24) return 'hace ${diff.inHours} hora${diff.inHours > 1 ? 's' : ''}';
    if (diff.inDays < 7) return 'hace ${diff.inDays} día${diff.inDays > 1 ? 's' : ''}';
    return Formatters.date(date);
  }

  /// Formatea teléfono para mostrar: "+51 987 654 321"
  static String phone(String phone) {
    if (phone.startsWith('+51')) {
      final cleaned = phone.replaceAll('+51', '');
      return '+51 ${cleaned.substring(0, 3)} ${cleaned.substring(3, 6)} ${cleaned.substring(6)}';
    }
    return phone;
  }

  /// Formatea distancia: "1.2 km" o "850 m"
  static String distance(double km) {
    if (km < 1) {
      return '${(km * 1000).round()} m';
    }
    return '${km.toStringAsFixed(1)} km';
  }

  /// Formatea duración: "5 min" o "1 h 30 min"
  static String duration(int minutes) {
    if (minutes < 60) return '$minutes min';
    final hours = minutes ~/ 60;
    final mins = minutes % 60;
    if (mins == 0) return '$hours h';
    return '$hours h $mins min';
  }

  /// Enmascara teléfono: "+51 ****** 4321"
  static String maskedPhone(String phone) {
    if (phone.length < 4) return phone;
    final last4 = phone.substring(phone.length - 4);
    return '+51 ****** $last4';
  }

  /// Iniciales del nombre: "Juan Quispe" -> "JQ"
  static String initials(String fullName) {
    final parts = fullName.trim().split(' ');
    if (parts.length < 2) return parts.first.substring(0, 1).toUpperCase();
    return '${parts.first[0]}${parts[1][0]}'.toUpperCase();
  }

  /// Traduce tipo de vehículo.
  static String vehicleType(String type) {
    switch (type) {
      case 'mototaxi':
        return 'Mototaxi';
      case 'car':
        return 'Auto';
      default:
        return type;
    }
  }

  /// Traduce estado de viaje.
  static String tripStatus(String status) {
    switch (status) {
      case 'searching':
        return 'Buscando conductor';
      case 'negotiating':
        return 'Revisando ofertas';
      case 'accepted':
        return 'Conductor en camino';
      case 'in_progress':
        return 'En curso';
      case 'completed':
        return 'Completado';
      case 'cancelled':
        return 'Cancelado';
      default:
        return status;
    }
  }

  /// Traduce estado de encomienda.
  static String packageStatus(String status) {
    switch (status) {
      case 'pending':
        return 'Esperando conductor';
      case 'assigned':
        return 'Conductor asignado';
      case 'picked_up':
        return 'Recogido';
      case 'in_transit':
        return 'En camino';
      case 'delivered':
        return 'Entregado';
      case 'cancelled':
        return 'Cancelado';
      default:
        return status;
    }
  }

  /// Traduce estado de conductor.
  static String driverStatus(String status) {
    switch (status) {
      case 'pending_docs':
        return 'Subiendo documentos';
      case 'under_review':
        return 'En revisión';
      case 'approved':
        return 'Aprobado';
      case 'rejected':
        return 'Rechazado';
      case 'suspended':
        return 'Suspendido';
      default:
        return status;
    }
  }
}