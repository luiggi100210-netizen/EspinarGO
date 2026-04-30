import 'dart:async';

import 'package:flutter/foundation.dart';
import 'package:flutter_secure_storage/flutter_secure_storage.dart';
import 'package:socket_io_client/socket_io_client.dart' as io;

import '../../../../core/constants/api_constants.dart';
import '../../../../core/constants/storage_keys.dart';
import '../../../../core/utils/logger.dart';

/// Servicio de WebSocket para comunicación en tiempo real.
/// Maneja la conexión con el backend para recibir ofertas y actualizaciones.
class TripWebSocketService {
  io.Socket? _socket;
  bool _isConnected = false;

  // Stream controllers
  final _newOfferController = StreamController<Map<String, dynamic>>.broadcast();
  final _tripUpdatedController = StreamController<Map<String, dynamic>>.broadcast();
  final _driverLocationController = StreamController<Map<String, dynamic>>.broadcast();
  final _driverArrivedController = StreamController<void>.broadcast();
  final _tripStartedController = StreamController<void>.broadcast();
  final _tripCompletedController = StreamController<void>.broadcast();

  // Streams públicos
  Stream<Map<String, dynamic>> get onNewOffer => _newOfferController.stream;
  Stream<Map<String, dynamic>> get onTripUpdated => _tripUpdatedController.stream;
  Stream<Map<String, dynamic>> get onDriverLocation => _driverLocationController.stream;
  Stream<void> get onDriverArrived => _driverArrivedController.stream;
  Stream<void> get onTripStarted => _tripStartedController.stream;
  Stream<void> get onTripCompleted => _tripCompletedController.stream;

  bool get isConnected => _isConnected;

  /// Conecta al WebSocket del servidor.
  Future<void> connect(String tripId) async {
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
      AppLogger.success('WebSocket conectado para viaje $tripId');

      // Unirse a la sala del viaje
      _socket?.emit('join_trip', {'trip_id': tripId});
    });

    _socket?.onDisconnect((_) {
      _isConnected = false;
      AppLogger.warning('WebSocket desconectado');
    });

    _socket?.onError((error) {
      AppLogger.error('WebSocket error', error: error);
    });

    // Escuchar eventos del servidor
    _socket?.on('new_offer', (data) {
      AppLogger.info('Nueva oferta recibida');
      _newOfferController.add(Map<String, dynamic>.from(data as Map));
    });

    _socket?.on('trip_updated', (data) {
      _tripUpdatedController.add(Map<String, dynamic>.from(data as Map));
    });

    _socket?.on('driver_location', (data) {
      _driverLocationController.add(Map<String, dynamic>.from(data as Map));
    });

    _socket?.on('driver_arrived', (_) {
      AppLogger.info('Conductor llegó al origen');
      _driverArrivedController.add(null);
    });

    _socket?.on('trip_started', (_) {
      AppLogger.info('Viaje iniciado');
      _tripStartedController.add(null);
    });

    _socket?.on('trip_completed', (_) {
      AppLogger.info('Viaje completado');
      _tripCompletedController.add(null);
    });
  }

  /// Desconecta del WebSocket.
  void disconnect() {
    _socket?.disconnect();
    _socket?.dispose();
    _socket = null;
    _isConnected = false;
  }

  /// Libera todos los recursos.
  void dispose() {
    disconnect();
    _newOfferController.close();
    _tripUpdatedController.close();
    _driverLocationController.close();
    _driverArrivedController.close();
    _tripStartedController.close();
    _tripCompletedController.close();
  }
}