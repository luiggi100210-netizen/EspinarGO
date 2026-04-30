import 'package:firebase_core/firebase_core.dart';
import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import 'app.dart';
import 'core/constants/app_constants.dart';

void main() async {
  // Asegurar que Flutter esté inicializado
  WidgetsFlutterBinding.ensureInitialized();

  // Inicializar Firebase (requiere google-services.json en Android y GoogleService-Info.plist en iOS)
  try {
    await Firebase.initializeApp();
  } catch (_) {
    // Firebase no configurado en este entorno
  }

  // Configurar orientación (solo portrait para Espinar)
  await SystemChrome.setPreferredOrientations([
    DeviceOrientation.portraitUp,
    DeviceOrientation.portraitDown,
  ]);

  // Configurar color de la barra de estado
  SystemChrome.setSystemUIOverlayStyle(
    const SystemUiOverlayStyle(
      statusBarColor: Colors.transparent,
      statusBarIconBrightness: Brightness.dark,
      statusBarBrightness: Brightness.light,
    ),
  );

  // Inicializar provider de Riverpod
  runApp(
    const ProviderScope(
      child: EspinarGoApp(),
    ),
  );
}