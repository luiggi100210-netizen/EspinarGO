# EspinarGo App

App móvil de transporte y encomiendas para Espinar, Cusco. Construida con Flutter, Riverpod y Google Maps.

## Requisitos

- Flutter 3.24+ (Dart 3.5+)
- Una clave de Google Maps API (Geocoding, Directions y Maps SDK for Android habilitados)

## Configuración de la API key

La clave de Google Maps **no está en el código fuente**: se inyecta en tiempo de compilación con `--dart-define` y llega tanto al código Dart (`MapsService`) como al `AndroidManifest.xml` (vía `build.gradle`).

1. Copia la plantilla y coloca tu clave:

   ```bash
   cp env.example.json env.json
   ```

   `env.json` está en `.gitignore` y nunca debe commitearse.

2. Ejecuta o compila pasando el archivo:

   ```bash
   # Desarrollo
   flutter run --dart-define-from-file=env.json

   # Release APK
   flutter build apk --release --dart-define-from-file=env.json
   ```

   También puedes pasar la clave directamente:

   ```bash
   flutter build apk --release --dart-define=GOOGLE_MAPS_API_KEY=tu_clave
   ```

> **Importante:** restringe la clave en Google Cloud Console por huella SHA-1 + nombre de paquete (`com.yauritaxi.app`) para que no pueda usarse fuera de la app.

## Comandos útiles

```bash
flutter pub get       # Instalar dependencias
flutter analyze       # Análisis estático
flutter test          # Ejecutar tests
```

## Estructura

```
lib/
├── core/        # Red (Dio), constantes, tema, utilidades
├── features/    # auth, driver, home, trips, packages, profile, ratings
│   └── <feature>/
│       ├── data/          # Servicios y modelos
│       ├── domain/        # Providers (Riverpod)
│       └── presentation/  # Pantallas y widgets
└── shared/      # Widgets compartidos
```
