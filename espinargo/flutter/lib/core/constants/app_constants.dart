/// Constantes globales de la aplicación.
/// Valores que no cambian y se usan en múltiples lugares.
class AppConstants {
  // Info de la app
  static const String APP_NAME = "EspinarGo";
  static const String APP_VERSION = "1.0.0";
  static const String SUPPORT_PHONE = "+51900000001";
  static const String SUPPORT_EMAIL = "soporte@espinargo.com";

  // Timeouts y tiempos (en milisegundos)
  static const int CONNECTION_TIMEOUT = 15000;
  static const int RECEIVE_TIMEOUT = 15000;
  static const int OTP_RESEND_SECONDS = 60;
  static const int TRIP_SEARCH_TIMEOUT_MINUTES = 10;

  // Paginación
  static const int DEFAULT_PAGE_SIZE = 20;
  static const int MAX_PAGE_SIZE = 50;

  // Coordenadas de Espinar, Cusco
  static const double ESPINAR_LAT = -14.7953;
  static const double ESPINAR_LNG = -71.4138;
  static const double DEFAULT_MAP_ZOOM = 15.0;
  static const double DRIVER_SEARCH_RADIUS_KM = 5.0;

  // Precios
  static const double MIN_TRIP_PRICE = 3.0;
  static const double MAX_TRIP_PRICE = 999.0;
  static const String CURRENCY_SYMBOL = "S/";
  static const String CURRENCY_CODE = "PEN";

  // Archivos
  static const int MAX_IMAGE_SIZE_MB = 5;
  static const int MAX_DOCUMENT_SIZE_MB = 10;
  static const List<String> ALLOWED_IMAGE_EXTENSIONS = ['jpg', 'jpeg', 'png'];

  // OTP
  static const int OTP_LENGTH = 6;
  static const int OTP_MAX_ATTEMPTS = 3;
}