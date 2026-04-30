/// Claves para flutter_secure_storage y shared_preferences.
/// Centraliza los nombres de las claves para evitar typos.
/// 
/// flutter_secure_storage: datos sensibles (tokens), cifrados
/// shared_preferences: datos no sensibles (configuración)
class StorageKeys {
  // Tokens - flutter_secure_storage (cifrado)
  static const String ACCESS_TOKEN = "access_token";
  static const String REFRESH_TOKEN = "refresh_token";

  // Usuario - shared_preferences (no sensible)
  static const String USER_ID = "user_id";
  static const String USER_NAME = "user_name";
  static const String USER_PHONE = "user_phone";
  static const String USER_ROLE = "user_role";
  static const String USER_AVATAR = "user_avatar";

  // Configuración
  static const String IS_FIRST_LAUNCH = "is_first_launch";
  static const String PREFERRED_LANG = "preferred_lang";
  static const String DARK_MODE = "dark_mode";
  static const String FCM_TOKEN = "fcm_token";
}