import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:google_maps_flutter/google_maps_flutter.dart';
import 'package:mocktail/mocktail.dart';

import 'package:espinargo_app/features/home/data/models/place_model.dart';
import 'package:espinargo_app/features/home/data/models/route_model.dart';
import 'package:espinargo_app/features/home/data/services/maps_service.dart';
import 'package:espinargo_app/features/home/domain/providers/map_provider.dart';

// ── Mocks ─────────────────────────────────────────────────────────────────────

class MockMapsService extends Mock implements MapsService {}

// ── Fixtures ──────────────────────────────────────────────────────────────────

PlaceModel _makePlace({
  String id = 'place-1',
  String name = 'Plaza de Armas',
  double lat = -14.832,
  double lng = -71.013,
}) =>
    PlaceModel(
      placeId: id,
      name: name,
      address: '$name, Espinar',
      lat: lat,
      lng: lng,
    );

RouteModel _makeRoute() => RouteModel(
      origin: _makePlace(id: 'origin'),
      destination: _makePlace(id: 'dest', name: 'Mercado Central', lat: -14.835, lng: -71.010),
      distanceKm: 1.5,
      durationMinutes: 8,
      polylinePoints: const [LatLng(-14.832, -71.013), LatLng(-14.835, -71.010)],
      suggestedPrice: 5.0,
      minPrice: 4.0,
      maxPrice: 7.0,
    );

// ── Helper ────────────────────────────────────────────────────────────────────

ProviderContainer _makeContainer(MockMapsService mockMaps) {
  return ProviderContainer(
    overrides: [
      mapsServiceProvider.overrideWithValue(mockMaps),
    ],
  );
}

// ── Tests ─────────────────────────────────────────────────────────────────────

void main() {
  late MockMapsService mockMaps;

  setUp(() {
    mockMaps = MockMapsService();
    registerFallbackValue(const LatLng(0, 0));
  });

  // ── build ──────────────────────────────────────────────────────────────────

  group('build', () {
    test('estado inicial → idle sin origen ni destino', () async {
      final container = _makeContainer(mockMaps);
      addTearDown(container.dispose);

      final state = await container.read(mapProvider.future);
      expect(state.mode, equals(MapMode.idle));
      expect(state.origin, isNull);
      expect(state.destination, isNull);
      expect(state.route, isNull);
    });
  });

  // ── setOrigin ──────────────────────────────────────────────────────────────

  group('setOrigin', () {
    test('sin destino previo → guarda origen, no calcula ruta', () async {
      final container = _makeContainer(mockMaps);
      addTearDown(container.dispose);
      await container.read(mapProvider.future);

      await container.read(mapProvider.notifier).setOrigin(_makePlace());

      final state = container.read(mapProvider).valueOrNull;
      expect(state?.origin?.placeId, equals('place-1'));
      expect(state?.route, isNull);
      verifyNever(() => mockMaps.getRoute(any(), any()));
    });

    test('con destino previo → calcula ruta automáticamente', () async {
      final dest = _makePlace(id: 'dest', name: 'Mercado', lat: -14.835, lng: -71.010);
      when(() => mockMaps.getRoute(any(), any()))
          .thenAnswer((_) async => _makeRoute());

      final container = _makeContainer(mockMaps);
      addTearDown(container.dispose);
      await container.read(mapProvider.future);

      // Inyectar destino previo
      container.read(mapProvider.notifier).state = AsyncValue.data(
        MapState(destination: dest),
      );

      await container.read(mapProvider.notifier).setOrigin(_makePlace());

      final state = container.read(mapProvider).valueOrNull;
      expect(state?.origin, isNotNull);
      expect(state?.route, isNotNull);
      expect(state?.mode, equals(MapMode.routeSelected));
      verify(() => mockMaps.getRoute(any(), any())).called(1);
    });
  });

  // ── setDestination ─────────────────────────────────────────────────────────

  group('setDestination', () {
    test('sin origen → guarda destino, no calcula ruta', () async {
      final container = _makeContainer(mockMaps);
      addTearDown(container.dispose);
      await container.read(mapProvider.future);

      await container.read(mapProvider.notifier).setDestination(_makePlace());

      final state = container.read(mapProvider).valueOrNull;
      expect(state?.destination?.placeId, equals('place-1'));
      expect(state?.route, isNull);
      verifyNever(() => mockMaps.getRoute(any(), any()));
    });

    test('con origen previo → calcula ruta', () async {
      final origin = _makePlace();
      when(() => mockMaps.getRoute(any(), any()))
          .thenAnswer((_) async => _makeRoute());

      final container = _makeContainer(mockMaps);
      addTearDown(container.dispose);
      await container.read(mapProvider.future);

      container.read(mapProvider.notifier).state = AsyncValue.data(
        MapState(origin: origin),
      );

      await container.read(mapProvider.notifier)
          .setDestination(_makePlace(id: 'dest', name: 'Mercado', lat: -14.835, lng: -71.010));

      final state = container.read(mapProvider).valueOrNull;
      expect(state?.destination, isNotNull);
      expect(state?.route, isNotNull);
      verify(() => mockMaps.getRoute(any(), any())).called(1);
    });

    test('API de ruta retorna null → ruta queda null, no lanza', () async {
      final origin = _makePlace();
      when(() => mockMaps.getRoute(any(), any())).thenAnswer((_) async => null);

      final container = _makeContainer(mockMaps);
      addTearDown(container.dispose);
      await container.read(mapProvider.future);

      container.read(mapProvider.notifier).state = AsyncValue.data(
        MapState(origin: origin),
      );

      await container.read(mapProvider.notifier)
          .setDestination(_makePlace(id: 'dest', lat: -14.835, lng: -71.010));

      final state = container.read(mapProvider).valueOrNull;
      expect(state?.route, isNull);
      expect(state?.isLoadingRoute, isFalse);
    });
  });

  // ── searchPlaces ───────────────────────────────────────────────────────────

  group('searchPlaces', () {
    test('query vacío → limpia resultados sin llamar al servicio', () async {
      final container = _makeContainer(mockMaps);
      addTearDown(container.dispose);
      await container.read(mapProvider.future);

      await container.read(mapProvider.notifier).searchPlaces('');

      verifyNever(() => mockMaps.searchPlaces(any()));
      final state = container.read(mapProvider).valueOrNull;
      expect(state?.searchResults, isEmpty);
      expect(state?.isSearching, isFalse);
    });

    test('query válido → devuelve resultados del servicio', () async {
      final places = [_makePlace(), _makePlace(id: 'place-2', name: 'Otra Plaza')];
      when(() => mockMaps.searchPlaces(any(), userLocation: any(named: 'userLocation')))
          .thenAnswer((_) async => places);

      final container = _makeContainer(mockMaps);
      addTearDown(container.dispose);
      await container.read(mapProvider.future);

      await container.read(mapProvider.notifier).searchPlaces('Plaza');

      final state = container.read(mapProvider).valueOrNull;
      expect(state?.searchResults, hasLength(2));
      expect(state?.isSearching, isFalse);
    });
  });

  // ── clearSearch ────────────────────────────────────────────────────────────

  group('clearSearch', () {
    test('limpia los resultados de búsqueda', () async {
      final container = _makeContainer(mockMaps);
      addTearDown(container.dispose);
      await container.read(mapProvider.future);

      container.read(mapProvider.notifier).state = AsyncValue.data(
        MapState(searchResults: [_makePlace()]),
      );

      container.read(mapProvider.notifier).clearSearch();

      final state = container.read(mapProvider).valueOrNull;
      expect(state?.searchResults, isEmpty);
    });
  });

  // ── clearRoute ─────────────────────────────────────────────────────────────

  group('clearRoute', () {
    test('limpia origen, destino y ruta → vuelve a idle', () async {
      final container = _makeContainer(mockMaps);
      addTearDown(container.dispose);
      await container.read(mapProvider.future);

      container.read(mapProvider.notifier).state = AsyncValue.data(
        MapState(
          mode: MapMode.routeSelected,
          origin: _makePlace(),
          destination: _makePlace(id: 'dest', lat: -14.835, lng: -71.010),
          route: _makeRoute(),
          selectedService: 'taxi',
        ),
      );

      container.read(mapProvider.notifier).clearRoute();

      final state = container.read(mapProvider).valueOrNull;
      expect(state?.mode, equals(MapMode.idle));
      expect(state?.origin, isNull);
      expect(state?.destination, isNull);
      expect(state?.route, isNull);
      // selectedService se preserva
      expect(state?.selectedService, equals('taxi'));
    });
  });

  // ── setSelectedService ─────────────────────────────────────────────────────

  group('setSelectedService', () {
    test('actualiza el servicio seleccionado', () async {
      final container = _makeContainer(mockMaps);
      addTearDown(container.dispose);
      await container.read(mapProvider.future);

      container.read(mapProvider.notifier).setSelectedService('taxi');

      final state = container.read(mapProvider).valueOrNull;
      expect(state?.selectedService, equals('taxi'));
    });
  });

  // ── setMapMode ─────────────────────────────────────────────────────────────

  group('setMapMode', () {
    test('cambia el modo del mapa', () async {
      final container = _makeContainer(mockMaps);
      addTearDown(container.dispose);
      await container.read(mapProvider.future);

      container.read(mapProvider.notifier).setMapMode(MapMode.selectingOrigin);

      final state = container.read(mapProvider).valueOrNull;
      expect(state?.mode, equals(MapMode.selectingOrigin));
    });
  });
}
