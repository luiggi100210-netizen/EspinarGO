import 'package:flutter/foundation.dart';

/// URLs y rutas de la API del backend.
/// La URL base se selecciona automáticamente según el entorno.
class ApiConstants {
  // URL base HTTP
  static const String _devUrl = "http://10.0.2.2:8000";
  static const String _prodUrl = "https://espinargo-api.up.railway.app";

  static String get BASE_URL => kReleaseMode ? _prodUrl : _devUrl;

  // URL WebSocket (ws:// en dev, wss:// en prod)
  static String get WS_URL =>
      kReleaseMode
          ? "wss://espinargo-api.up.railway.app"
          : "ws://10.0.2.2:8000";

  static const String API_VERSION = "/api/v1";

  // Prefijos de módulos
  static const String AUTH = "/api/v1/auth";
  static const String USERS = "/api/v1/users";
  static const String TRIPS = "/api/v1/trips";
  static const String PACKAGES = "/api/v1/packages";
  static const String RATINGS = "/api/v1/ratings";

  // Endpoints de AUTH
  static const String REGISTER = "/register";
  static const String LOGIN = "/login";
  static const String LOGOUT = "/logout";
  static const String LOGOUT_ALL = "/logout-all";
  static const String SEND_OTP = "/send-otp";
  static const String VERIFY_PHONE = "/verify-phone";
  static const String REFRESH_TOKEN = "/refresh";
  static const String ME = "/me";
  static const String FORGOT_PASSWORD = "/forgot-password";
  static const String RESET_PASSWORD = "/reset-password";
  static const String CHANGE_PASSWORD = "/change-password";

  // Endpoints de TRIPS
  static const String ACTIVE = "/active";
  static const String HISTORY = "/history";

  // Endpoints del conductor
  static const String MY_DRIVER_PROFILE = '/api/v1/users/me/driver-profile';
  static const String DRIVER_ONLINE_STATUS = '/api/v1/users/me/online';
  static const String DRIVER_EARNINGS = '/api/v1/trips/driver/earnings';
  static const String DEVICE_TOKEN = '/api/v1/users/me/device-token';

  // Helpers para construir URLs
  static String tripById(String id) => "/api/v1/trips/$id";
  static String tripOffers(String id) => "/api/v1/trips/$id/offers";
  static String acceptOffer(String id) => "/api/v1/trips/$id/accept-offer";
  static const String MAKE_OFFER = "/api/v1/trips/offer";
  static String startTrip(String id) => "/api/v1/trips/$id/start";
  static String completeTrip(String id) => "/api/v1/trips/$id/complete";
  static String cancelTrip(String id) => "/api/v1/trips/$id/cancel";
  static String trackPackage(String code) => "/api/v1/packages/track/$code";
  static String driverProfile(String id) => "/api/v1/users/drivers/$id";
  static String wsDriver() => "${WS_URL}/ws/driver";
  static String wsTrip(String tripId) => "${WS_URL}/ws/trips/$tripId";
}
