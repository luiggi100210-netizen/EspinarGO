import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_secure_storage/flutter_secure_storage.dart';
import 'package:shared_preferences/shared_preferences.dart';

import '../core/constants/storage_keys.dart';
import '../core/network/dio_client.dart';

/// Proveedor de DioClient - cliente HTTP para la API
final dioClientProvider = Provider<DioClient>((ref) {
  return DioClient();
});

/// Proveedor de FlutterSecureStorage - storage cifrado
final secureStorageProvider = Provider<FlutterSecureStorage>((ref) {
  return const FlutterSecureStorage();
});

/// Proveedor de SharedPreferences - storage no cifrado
/// Se inicializa async, usar con .when() o .future
final sharedPreferencesProvider = FutureProvider<SharedPreferences>((ref) async {
  return await SharedPreferences.getInstance();
});

/// Estado global de la app
class AppState {
  final bool isFirstLaunch;
  final String preferredLang;
  final bool darkMode;

  const AppState({
    this.isFirstLaunch = true,
    this.preferredLang = 'es',
    this.darkMode = false,
  });

  AppState copyWith({
    bool? isFirstLaunch,
    String? preferredLang,
    bool? darkMode,
  }) {
    return AppState(
      isFirstLaunch: isFirstLaunch ?? this.isFirstLaunch,
      preferredLang: preferredLang ?? this.preferredLang,
      darkMode: darkMode ?? this.darkMode,
    );
  }
}

/// Provider de estado global de la app
final appStateProvider = StateNotifierProvider<AppStateNotifier, AppState>((ref) {
  return AppStateNotifier();
});

class AppStateNotifier extends StateNotifier<AppState> {
  AppStateNotifier() : super(const AppState());

  Future<void> loadFromStorage() async {
    final prefs = await SharedPreferences.getInstance();
    state = AppState(
      isFirstLaunch: prefs.getBool(StorageKeys.IS_FIRST_LAUNCH) ?? true,
      preferredLang: prefs.getString(StorageKeys.PREFERRED_LANG) ?? 'es',
      darkMode: prefs.getBool(StorageKeys.DARK_MODE) ?? false,
    );
  }

  void setFirstLaunch(bool value) {
    state = state.copyWith(isFirstLaunch: value);
  }

  Future<void> setDarkMode(bool value) async {
    state = state.copyWith(darkMode: value);
    final prefs = await SharedPreferences.getInstance();
    await prefs.setBool(StorageKeys.DARK_MODE, value);
  }
}
