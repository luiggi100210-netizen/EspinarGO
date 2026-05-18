import 'dart:async';
import 'dart:convert';

import 'package:flutter_secure_storage/flutter_secure_storage.dart';
import 'package:web_socket_channel/web_socket_channel.dart';

import '../../../../core/constants/api_constants.dart';
import '../../../../core/constants/storage_keys.dart';
import '../../../../core/utils/logger.dart';

/// WebSocket para seguimiento de viaje en tiempo real.
/// Protocolo WS nativo compatible con FastAPI.
/// Autenticación: primer mensaje {"type": "auth", "token": "..."}
class TripWebSocketService {
  WebSocketChannel? _channel;
  StreamSubscription? _subscription;
  bool _isConnected = false;

  final _newOfferController =
      StreamController<Map<String, dynamic>>.broadcast();
  final _tripUpdatedController =
      StreamController<Map<String, dynamic>>.broadcast();
  final _driverLocationController =
      StreamController<Map<String, dynamic>>.broadcast();
  final _tripStartedController = StreamController<void>.broadcast();
  final _tripCompletedController = StreamController<void>.broadcast();

  Stream<Map<String, dynamic>> get onNewOffer => _newOfferController.stream;
  Stream<Map<String, dynamic>> get onTripUpdated =>
      _tripUpdatedController.stream;
  Stream<Map<String, dynamic>> get onDriverLocation =>
      _driverLocationController.stream;
  Stream<void> get onTripStarted => _tripStartedController.stream;
  Stream<void> get onTripCompleted => _tripCompletedController.stream;

  bool get isConnected => _isConnected;

  Future<void> connect(String tripId) async {
    const secureStorage = FlutterSecureStorage();
    final token =
        await secureStorage.read(key: StorageKeys.ACCESS_TOKEN) ?? '';

    try {
      _channel = WebSocketChannel.connect(
        Uri.parse(ApiConstants.wsTrip(tripId)),
      );

      // Handshake de autenticación como primer mensaje
      _channel!.sink.add(jsonEncode({'type': 'auth', 'token': token}));
      _isConnected = true;
      AppLogger.success('Trip WebSocket conectado para viaje $tripId');

      _subscription = _channel!.stream.listen(
        _handleMessage,
        onDone: () {
          _isConnected = false;
          AppLogger.warning('Trip WebSocket desconectado');
        },
        onError: (error) {
          AppLogger.error('Trip WebSocket error', error: error);
          _isConnected = false;
        },
        cancelOnError: false,
      );
    } catch (e) {
      AppLogger.error('Trip WebSocket fallo de conexión', error: e);
      _isConnected = false;
    }
  }

  void _handleMessage(dynamic raw) {
    try {
      final data = jsonDecode(raw as String) as Map<String, dynamic>;
      final type = data['type'] as String?;

      switch (type) {
        case 'new_offer':
          AppLogger.info('Nueva oferta recibida');
          _newOfferController.add(data);
        case 'trip_update':
          _tripUpdatedController.add(data);
          final status = data['status'] as String?;
          if (status == 'in_progress') {
            _tripStartedController.add(null);
          } else if (status == 'completed') {
            _tripCompletedController.add(null);
          }
        case 'driver_location':
          _driverLocationController.add(data);
      }
    } catch (e) {
      AppLogger.error('Error procesando mensaje WS viaje', error: e);
    }
  }

  void disconnect() {
    _subscription?.cancel();
    _channel?.sink.close();
    _channel = null;
    _isConnected = false;
  }

  void dispose() {
    disconnect();
    _newOfferController.close();
    _tripUpdatedController.close();
    _driverLocationController.close();
    _tripStartedController.close();
    _tripCompletedController.close();
  }
}
