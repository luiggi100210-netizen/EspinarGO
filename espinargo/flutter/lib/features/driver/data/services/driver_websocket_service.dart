import 'dart:async';

import 'package:flutter_secure_storage/flutter_secure_storage.dart';
import 'package:socket_io_client/socket_io_client.dart' as io;

import '../../../../core/constants/api_constants.dart';
import '../../../../core/constants/storage_keys.dart';
import '../../../../core/utils/logger.dart';

/// WebSocket del lado del conductor.
/// Recibe solicitudes de viaje en tiempo real.
class DriverWebSocketService {
  io.Socket? _socket;
  bool _isConnected = false;

  final _newTripRequestController = StreamController<Map<String, dynamic>>.broadcast();
  final _tripCancelledController = StreamController<String>.broadcast();
  final _offerAcceptedController = StreamController<Map<String, dynamic>>.broadcast();
  final _passengerLocationController = StreamController<Map<String, dynamic>>.broadcast();

  Stream<Map<String, dynamic>> get onNewTripRequest => _newTripRequestController.stream;
  Stream<String> get onTripCancelled => _tripCancelledController.stream;
  Stream<Map<String, dynamic>> get onOfferAccepted => _offerAcceptedController.stream;
  Stream<Map<String, dynamic>> get onPassengerLocation => _passengerLocationController.stream;

  bool get isConnected => _isConnected;

  /// Conectar al WebSocket del servidor.
  Future<void> connect() async {
    const secureStorage = FlutterSecureStorage();
    final token = await secureStorage.read(key: StorageKeys.ACCESS_TOKEN) ?? '';

    _socket = io.io(
      ApiConstants.WS_URL,
      io.OptionBuilder()
          .setTransports(['websocket'])
          .enableAutoConnect()
          .setAuth({'token': token})
          .build(),
    );

    _socket?.onConnect((_) {
      _isConnected = true;
      AppLogger.success('Driver WebSocket conectado');
      _socket?.emit('driver_online');
    });

    _socket?.onDisconnect((_) {
      _isConnected = false;
      AppLogger.warning('Driver WebSocket desconectado');
    });

    _socket?.onError((error) {
      AppLogger.error('Driver WebSocket error', error: error);
    });

    _socket?.on('new_trip_request', (data) {
      AppLogger.info('Nueva solicitud de viaje recibida');
      _newTripRequestController.add(Map<String, dynamic>.from(data as Map));
    });

    _socket?.on('trip_cancelled', (data) {
      final tripId = data['trip_id'] as String;
      _tripCancelledController.add(tripId);
    });

    _socket?.on('offer_accepted', (data) {
      AppLogger.info('Oferta aceptada');
      _offerAcceptedController.add(Map<String, dynamic>.from(data as Map));
    });

    _socket?.on('passenger_location', (data) {
      _passengerLocationController.add(Map<String, dynamic>.from(data as Map));
    });
  }

  /// Actualizar ubicación del conductor.
  void updateLocation(double lat, double lng) {
    if (_isConnected) {
      _socket?.emit('driver_location_update', {'lat': lat, 'lng': lng});
    }
  }

  /// Desconectar.
  void disconnect() {
    if (_isConnected) {
      _socket?.emit('driver_offline');
    }
    _socket?.disconnect();
    _socket?.dispose();
    _socket = null;
    _isConnected = false;
  }

  /// Liberar recursos.
  void dispose() {
    disconnect();
    _newTripRequestController.close();
    _tripCancelledController.close();
    _offerAcceptedController.close();
    _passengerLocationController.close();
  }
}