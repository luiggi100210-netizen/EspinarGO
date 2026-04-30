/// URLs y rutas de la API del backend.
/// Si cambia la URL base, solo se cambia aquí.
class ApiConstants {
  // En desarrollo: 10.0.2.2 es localhost del emulador Android
  // En iOS usar: http://localhost:8000
  // En producción usar la URL de Railway
  static const String BASE_URL = "http://10.0.2.2:8000";

  // URL de WebSocket para tiempo real
  static const String WS_URL = "http://10.0.2.2:8000";

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
  static const String CREATE = "";
  static const String ACTIVE = "/active";
  static const String HISTORY = "/history";
  static const String OFFER = "/offer";

  // Helpers para construir URLs
  static String tripById(String id) => "/api/v1/trips/$id";
  static String tripOffers(String id) => "/api/v1/trips/$id/offers";
  static String acceptOffer(String id) => "/api/v1/trips/$id/accept-offer";
  static String startTrip(String id) => "/api/v1/trips/$id/start";
  static String completeTrip(String id) => "/api/v1/trips/$id/complete";
  static String cancelTrip(String id) => "/api/v1/trips/$id/cancel";
  static String trackPackage(String code) => "/api/v1/packages/track/$code";
  static String driverProfile(String id) => "/api/v1/users/drivers/$id";
}