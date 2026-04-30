import 'package:dio/dio.dart';

import '../../../../core/constants/api_constants.dart';
import '../../../../core/network/dio_client.dart';
import '../models/package_model.dart';
import '../models/tracking_event_model.dart';

/// Repositorio de encomiendas.
class PackageRepository {
  final DioClient _dioClient;

  PackageRepository({required DioClient dioClient}) : _dioClient = dioClient;

  /// Crea una nueva encomienda.
  Future<PackageModel> createPackage({
    required String recipientName,
    required String recipientPhone,
    required String deliveryAddress,
    required String size,
    required String description,
    bool isFragile = false,
    String paymentMethod = 'cash',
  }) async {
    try {
      final response = await _dioClient.post(
        ApiConstants.PACKAGES,
        data: {
          'recipient_name': recipientName,
          'recipient_phone': recipientPhone,
          'delivery_address': deliveryAddress,
          'size': size,
          'description': description,
          'is_fragile': isFragile,
          'payment_method': paymentMethod,
        },
      );
      return PackageModel.fromJson(response.data as Map<String, dynamic>);
    } on DioException catch (e) {
      throw Exception(_handleError(e));
    }
  }

  /// Rastrea una encomienda por código.
  Future<Map<String, dynamic>> trackPackage(String code) async {
    try {
      final response = await _dioClient.get(ApiConstants.trackPackage(code));
      final data = response.data as Map<String, dynamic>;
      return {
        'package': PackageModel.fromJson(data['package'] as Map<String, dynamic>),
        'tracking_history': (data['tracking_history'] as List<dynamic>)
            .map((e) => TrackingEventModel.fromJson(e as Map<String, dynamic>))
            .toList(),
      };
    } on DioException catch (e) {
      if (e.response?.statusCode == 404) {
        throw Exception('Código de seguimiento inválido. Verifica que el código es correcto.');
      }
      throw Exception(_handleError(e));
    }
  }

  /// Obtiene las encomiendas del usuario.
  Future<List<PackageModel>> getMyPackages({int page = 1, int perPage = 20}) async {
    try {
      final response = await _dioClient.get(
        '${ApiConstants.PACKAGES}/my',
        queryParameters: {'page': page, 'per_page': perPage},
      );
      final data = response.data as List<dynamic>;
      return data.map((json) => PackageModel.fromJson(json as Map<String, dynamic>)).toList();
    } on DioException catch (e) {
      throw Exception(_handleError(e));
    }
  }

  /// Obtiene una encomienda por ID.
  Future<PackageModel> getPackageById(String id) async {
    try {
      final response = await _dioClient.get('${ApiConstants.PACKAGES}/$id');
      return PackageModel.fromJson(response.data as Map<String, dynamic>);
    } on DioException catch (e) {
      throw Exception(_handleError(e));
    }
  }

  String _handleError(DioException e) {
    if (e.response?.data != null && e.response?.data is Map) {
      final data = e.response?.data as Map<String, dynamic>;
      if (data['detail'] != null) return data['detail'] as String;
      if (data['message'] != null) return data['message'] as String;
    }
    switch (e.response?.statusCode) {
      case 400:
        return 'Datos inválidos';
      case 404:
        return 'No encontrado';
      case 500:
        return 'Error del servidor';
      default:
        return 'Sin conexión';
    }
  }
}