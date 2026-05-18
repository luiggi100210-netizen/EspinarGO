import 'dart:async';
import 'dart:convert';

import 'package:flutter_secure_storage/flutter_secure_storage.dart';
import 'package:web_socket_channel/web_socket_channel.dart';

import '../../../../core/constants/api_constants.dart';
import '../../../../core/constants/storage_keys.dart';
import '../../../../core/utils/logger.dart';

/// WebSocket del conductor.
/// Protocolo WS nativo compatible con FastAPI.
/// Autenticación: primer mensaje {"type": "auth", "token": "..."}
class DriverWebSocketService {
  WebSocketChannel? _channel;
  StreamSubscription? _subscription;
  bool _isConnected = false;

  final _newTripRequestController =
      StreamController<Map<String, dynamic>>.broadcast();
  final _tripCancelledController = StreamController<String>.broadcast();
  final _offerAcceptedController =
      StreamController<Map<String, dynamic>>.broadcast();

  Stream<Map<String, dynamic>> get onNewTripRequest =>
      _newTripRequestController.stream;
  Stream<String> get onTripCancelled => _tripCancelledController.stream;
  Stream<Map<String, dynamic>> get onOfferAccepted =>
      _offerAcceptedController.stream;

  bool get isConnected => _isConnected;

  Future<void> connect() async {
    const secureStorage = FlutterSecureStorage();
    final token =
        await secureStorage.read(key: StorageKeys.ACCESS_TOKEN) ?? '';

    try {
      _channel = WebSocketChannel.connect(Uri.parse(ApiConstants.wsDriver()));

      // Handshake de autenticación como primer mensaje
      _channel!.sink.add(jsonEncode({'type': 'auth', 'token': token}));
      _isConnected = true;
      AppLogger.success('Driver WebSocket conectado');

      _subscription = _channel!.stream.listen(
        _handleMessage,
        onDone: _onDisconnected,
        onError: (error) {
          AppLogger.error('Driver WebSocket error', error: error);
          _isConnected = false;
        },
        cancelOnError: false,
      );
    } catch (e) {
      AppLogger.error('Driver WebSocket fallo de conexión', error: e);
      _isConnected = false;
    }
  }

  void _handleMessage(dynamic raw) {
    try {
      final data = jsonDecode(raw as String) as Map<String, dynamic>;
      final type = data['type'] as String?;

      switch (type) {
        case 'new_trip':
          AppLogger.info('Nueva solicitud de viaje recibida');
          _newTripRequestController.add(data);
        case 'trip_update':
          if (data['status'] == 'cancelled') {
            _tripCancelledController.add(data['trip_id'] as String? ?? '');
          }
        case 'offer_accepted':
          AppLogger.info('Oferta aceptada');
          _offerAcceptedController.add(data);
      }
    } catch (e) {
      AppLogger.error('Error procesando mensaje WS conductor', error: e);
    }
  }

  void _onDisconnected() {
    _isConnected = false;
    AppLogger.warning('Driver WebSocket desconectado');
  }

  void updateLocation(double lat, double lng) {
    if (_isConnected) {
      _channel?.sink.add(jsonEncode({
        'type': 'location',
        'lat': lat.toString(),
        'lng': lng.toString(),
      }));
    }
  }

  void setOnlineStatus(bool isOnline) {
    if (_isConnected) {
      _channel?.sink.add(jsonEncode({'type': 'online', 'status': isOnline}));
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
    _newTripRequestController.close();
    _tripCancelledController.close();
    _offerAcceptedController.close();
  }
}
