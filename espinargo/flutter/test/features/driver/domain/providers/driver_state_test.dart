import 'package:flutter_test/flutter_test.dart';
import 'package:espinargo_app/features/driver/data/models/driver_profile_model.dart';
import 'package:espinargo_app/features/driver/domain/providers/driver_state.dart';

DriverProfileModel _makeProfile({
  String driverStatus = 'approved',
  bool isOnline = true,
}) =>
    DriverProfileModel(
      id: 'dp-1',
      userId: 'u-1',
      driverStatus: driverStatus,
      isOnline: isOnline,
      vehicleType: 'mototaxi',
    );

void main() {
  group('DriverState factories', () {
    test('estado por defecto — offline, sin perfil, sin loading', () {
      const state = DriverState();
      expect(state.flowStatus, equals(DriverFlowStatus.offline));
      expect(state.driverProfile, isNull);
      expect(state.isLoading, isFalse);
      expect(state.errorMessage, isNull);
      expect(state.todayEarnings, equals(0));
      expect(state.todayTrips, equals(0));
      expect(state.pendingRequests, isEmpty);
    });

    test('online — tiene perfil y status online', () {
      final profile = _makeProfile();
      final state = DriverState.online(profile);
      expect(state.flowStatus, equals(DriverFlowStatus.online));
      expect(state.driverProfile, equals(profile));
      expect(state.isLoading, isFalse);
    });

    test('error — estado error con mensaje', () {
      final state = DriverState.error('Sin conexión');
      expect(state.flowStatus, equals(DriverFlowStatus.error));
      expect(state.errorMessage, equals('Sin conexión'));
      expect(state.isLoading, isFalse);
    });
  });

  group('DriverState getters', () {
    test('isOnline es false en estado offline', () {
      expect(const DriverState().isOnline, isFalse);
    });

    test('isOnline es false en estado goingOnline', () {
      const state = DriverState(flowStatus: DriverFlowStatus.goingOnline);
      expect(state.isOnline, isFalse);
    });

    test('isOnline es true en estado online', () {
      final state = DriverState.online(_makeProfile());
      expect(state.isOnline, isTrue);
    });

    test('isOnline es true en estado receivedRequest', () {
      const state = DriverState(flowStatus: DriverFlowStatus.receivedRequest);
      expect(state.isOnline, isTrue);
    });

    test('isOnline es true en estado passengerOnboard', () {
      const state = DriverState(flowStatus: DriverFlowStatus.passengerOnboard);
      expect(state.isOnline, isTrue);
    });

    test('hasActiveTrip es false sin viaje', () {
      expect(const DriverState().hasActiveTrip, isFalse);
    });

    test('hasPendingRequests es false cuando lista vacía', () {
      expect(const DriverState().hasPendingRequests, isFalse);
    });

    test('hasPendingRequests es true cuando hay solicitudes', () {
      const state = DriverState(pendingRequests: [
        {'trip_id': 'trip-1'}
      ]);
      expect(state.hasPendingRequests, isTrue);
    });

    test('pendingRequestsCount retorna cantidad correcta', () {
      const state = DriverState(pendingRequests: [
        {'trip_id': 'trip-1'},
        {'trip_id': 'trip-2'},
      ]);
      expect(state.pendingRequestsCount, equals(2));
    });
  });

  group('DriverState.statusMessage', () {
    test('offline — desconectado', () {
      expect(
          const DriverState().statusMessage, equals('Estás desconectado'));
    });

    test('goingOnline — conectando', () {
      const state = DriverState(flowStatus: DriverFlowStatus.goingOnline);
      expect(state.statusMessage, contains('Conectando'));
    });

    test('online — disponible esperando', () {
      final state = DriverState.online(_makeProfile());
      expect(state.statusMessage, contains('Disponible'));
    });

    test('receivedRequest — nueva solicitud', () {
      const state = DriverState(flowStatus: DriverFlowStatus.receivedRequest);
      expect(state.statusMessage, contains('solicitud'));
    });

    test('negotiating — oferta enviada', () {
      const state = DriverState(flowStatus: DriverFlowStatus.negotiating);
      expect(state.statusMessage, contains('Oferta'));
    });

    test('offerAccepted — pasajero aceptó', () {
      const state = DriverState(flowStatus: DriverFlowStatus.offerAccepted);
      expect(state.statusMessage, contains('aceptó'));
    });

    test('goingToPassenger — en camino', () {
      const state =
          DriverState(flowStatus: DriverFlowStatus.goingToPassenger);
      expect(state.statusMessage, contains('camino'));
    });

    test('passengerOnboard — viaje en curso', () {
      const state = DriverState(flowStatus: DriverFlowStatus.passengerOnboard);
      expect(state.statusMessage, contains('curso'));
    });

    test('completed — viaje completado', () {
      const state = DriverState(flowStatus: DriverFlowStatus.completed);
      expect(state.statusMessage, contains('completado'));
    });

    test('error — muestra el mensaje de error', () {
      final state = DriverState.error('Timeout de conexión');
      expect(state.statusMessage, equals('Timeout de conexión'));
    });

    test('error sin mensaje — fallback a "Error"', () {
      const state = DriverState(flowStatus: DriverFlowStatus.error);
      expect(state.statusMessage, equals('Error'));
    });
  });

  group('DriverState.copyWith', () {
    test('actualiza solo los campos indicados', () {
      const state = DriverState(flowStatus: DriverFlowStatus.offline);
      final updated = state.copyWith(
        flowStatus: DriverFlowStatus.online,
        isLoading: true,
      );
      expect(updated.flowStatus, equals(DriverFlowStatus.online));
      expect(updated.isLoading, isTrue);
      expect(updated.driverProfile, isNull);
      expect(updated.todayEarnings, equals(0));
    });

    test('errorMessage se puede pasar null para limpiar', () {
      const state = DriverState(errorMessage: 'Previo');
      final cleared = state.copyWith(errorMessage: null);
      expect(cleared.errorMessage, isNull);
    });

    test('preserva pendingRequests existentes', () {
      const state = DriverState(pendingRequests: [
        {'trip_id': 'trip-1'}
      ]);
      final updated = state.copyWith(isLoading: false);
      expect(updated.pendingRequests, hasLength(1));
    });

    test('actualiza todayEarnings y todayTrips', () {
      const state = DriverState();
      final updated = state.copyWith(todayEarnings: 25.50, todayTrips: 3);
      expect(updated.todayEarnings, equals(25.50));
      expect(updated.todayTrips, equals(3));
    });
  });
}
