import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:geolocator/geolocator.dart';
import 'package:plugin_platform_interface/plugin_platform_interface.dart';

import 'package:espinargo_app/features/home/domain/providers/location_provider.dart';

// ── Stub de GeolocatorPlatform ─────────────────────────────────────────────

class _StubGeolocator extends GeolocatorPlatform with MockPlatformInterfaceMixin {
  final bool gpsEnabled;
  final LocationPermission checkPermissionResult;
  final LocationPermission requestPermissionResult;
  final Position? positionResult;
  final bool throwOnPosition;

  _StubGeolocator({
    required this.gpsEnabled,
    this.checkPermissionResult = LocationPermission.whileInUse,
    this.requestPermissionResult = LocationPermission.whileInUse,
    this.positionResult,
    this.throwOnPosition = false,
  });

  @override
  Future<bool> isLocationServiceEnabled() async => gpsEnabled;

  @override
  Future<LocationPermission> checkPermission() async => checkPermissionResult;

  @override
  Future<LocationPermission> requestPermission() async => requestPermissionResult;

  @override
  Future<Position> getCurrentPosition({LocationSettings? locationSettings}) async {
    if (throwOnPosition) throw Exception('timeout');
    return positionResult!;
  }

  @override
  Future<bool> openAppSettings() async => true;

  @override
  Stream<Position> getPositionStream({LocationSettings? locationSettings}) =>
      const Stream.empty();
}

// ── Fixture ────────────────────────────────────────────────────────────────

Position _makePosition({double lat = -14.832, double lng = -71.013}) => Position(
      latitude: lat,
      longitude: lng,
      timestamp: DateTime.utc(2024),
      altitude: 3900.0,
      altitudeAccuracy: 0.0,
      accuracy: 5.0,
      heading: 0.0,
      headingAccuracy: 0.0,
      speed: 0.0,
      speedAccuracy: 0.0,
    );

// ── Helpers ────────────────────────────────────────────────────────────────

ProviderContainer _makeContainer() =>
    ProviderContainer();

void _stubGeolocator(_StubGeolocator stub) {
  GeolocatorPlatform.instance = stub;
}

// ── Tests ──────────────────────────────────────────────────────────────────

void main() {
  setUpAll(() {
    TestWidgetsFlutterBinding.ensureInitialized();
  });

  // ── build: GPS deshabilitado ───────────────────────────────────────────────

  group('build - GPS deshabilitado', () {
    test('estado inicial refleja GPS apagado y usa espinarCenter', () async {
      _stubGeolocator(_StubGeolocator(gpsEnabled: false));
      final container = _makeContainer();
      addTearDown(container.dispose);

      final state = await container.read(locationProvider.future);

      expect(state.isGpsEnabled, isFalse);
      expect(state.hasPermission, isFalse);
      expect(state.errorMessage, contains('GPS'));
      expect(state.currentLatLng, isNotNull); // espinarCenter
      expect(state.currentLatLng!.latitude, closeTo(-14.7953, 0.001));
    });
  });

  // ── build: GPS habilitado, permiso denegado ────────────────────────────────

  group('build - permiso denegado', () {
    test('hasPermission = false, usa espinarCenter', () async {
      _stubGeolocator(_StubGeolocator(
        gpsEnabled: true,
        checkPermissionResult: LocationPermission.denied,
        requestPermissionResult: LocationPermission.denied,
      ));
      final container = _makeContainer();
      addTearDown(container.dispose);

      final state = await container.read(locationProvider.future);

      expect(state.isGpsEnabled, isTrue);
      expect(state.hasPermission, isFalse);
      expect(state.errorMessage, isNotNull);
      expect(state.currentLatLng, isNotNull);
    });
  });

  // ── build: GPS habilitado, permiso concedido, posición obtenida ───────────

  group('build - posición obtenida', () {
    test('currentPosition y currentLatLng son correctos', () async {
      final position = _makePosition(lat: -14.832, lng: -71.013);
      _stubGeolocator(_StubGeolocator(
        gpsEnabled: true,
        checkPermissionResult: LocationPermission.whileInUse,
        positionResult: position,
      ));
      final container = _makeContainer();
      addTearDown(container.dispose);

      final state = await container.read(locationProvider.future);

      expect(state.isGpsEnabled, isTrue);
      expect(state.hasPermission, isTrue);
      expect(state.currentPosition, isNotNull);
      expect(state.currentLatLng!.latitude, closeTo(-14.832, 0.001));
      expect(state.errorMessage, isNull);
    });
  });

  // ── build: GPS habilitado, posición falla ─────────────────────────────────

  group('build - posición falla', () {
    test('errorMessage no nulo, usa espinarCenter', () async {
      _stubGeolocator(_StubGeolocator(
        gpsEnabled: true,
        checkPermissionResult: LocationPermission.whileInUse,
        throwOnPosition: true,
      ));
      final container = _makeContainer();
      addTearDown(container.dispose);

      final state = await container.read(locationProvider.future);

      expect(state.isGpsEnabled, isTrue);
      expect(state.hasPermission, isTrue);
      expect(state.currentPosition, isNull);
      expect(state.errorMessage, isNotNull);
      expect(state.currentLatLng, isNotNull); // espinarCenter
    });
  });

  // ── requestPermissionAndGetLocation ───────────────────────────────────────

  group('requestPermissionAndGetLocation', () {
    test('GPS apagado → isGpsEnabled = false', () async {
      _stubGeolocator(_StubGeolocator(gpsEnabled: false));
      final container = _makeContainer();
      addTearDown(container.dispose);
      await container.read(locationProvider.future);

      _stubGeolocator(_StubGeolocator(gpsEnabled: false));
      await container.read(locationProvider.notifier).requestPermissionAndGetLocation();

      final state = container.read(locationProvider).valueOrNull;
      expect(state?.isGpsEnabled, isFalse);
    });

    test('GPS activo, permiso concedido → actualiza currentPosition', () async {
      final pos = _makePosition(lat: -14.832, lng: -71.013);
      _stubGeolocator(_StubGeolocator(
        gpsEnabled: true,
        checkPermissionResult: LocationPermission.whileInUse,
        positionResult: pos,
      ));
      final container = _makeContainer();
      addTearDown(container.dispose);
      await container.read(locationProvider.future);

      await container.read(locationProvider.notifier).requestPermissionAndGetLocation();

      final state = container.read(locationProvider).valueOrNull;
      expect(state?.currentPosition, isNotNull);
      expect(state?.hasPermission, isTrue);
    });
  });

  // ── mapCenter ─────────────────────────────────────────────────────────────

  group('mapCenter', () {
    test('sin ubicación → retorna espinarCenter', () async {
      _stubGeolocator(_StubGeolocator(gpsEnabled: false));
      final container = _makeContainer();
      addTearDown(container.dispose);
      await container.read(locationProvider.future);

      final center = container.read(locationProvider.notifier).mapCenter;
      expect(center.latitude, closeTo(-14.7953, 0.001));
    });

    test('con ubicación → retorna currentLatLng', () async {
      final pos = _makePosition(lat: -14.832, lng: -71.013);
      _stubGeolocator(_StubGeolocator(
        gpsEnabled: true,
        checkPermissionResult: LocationPermission.whileInUse,
        positionResult: pos,
      ));
      final container = _makeContainer();
      addTearDown(container.dispose);
      await container.read(locationProvider.future);

      final center = container.read(locationProvider.notifier).mapCenter;
      expect(center.latitude, closeTo(-14.832, 0.001));
    });
  });
}
