import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../../../core/providers.dart';
import '../../data/repositories/package_repository.dart';
import '../../data/models/package_model.dart';
import '../../data/models/tracking_event_model.dart';
import 'package_state.dart';

/// Provider del repositorio de paquetes.
final packageRepositoryProvider = Provider<PackageRepository>((ref) {
  final dioClient = ref.watch(dioClientProvider);
  return PackageRepository(dioClient: dioClient);
});

/// Provider de paquetes.
final packageProvider = AsyncNotifierProvider<PackageNotifier, PackageState>(() {
  return PackageNotifier();
});

/// Notificador de paquetes.
class PackageNotifier extends AsyncNotifier<PackageState> {
  @override
  Future<PackageState> build() async {
    return _loadMyPackages();
  }

  Future<PackageState> _loadMyPackages() async {
    try {
      final repo = ref.read(packageRepositoryProvider);
      final packages = await repo.getMyPackages();
      return PackageState(myPackages: packages);
    } catch (e) {
      return const PackageState();
    }
  }

  /// Crea una nueva encomienda.
  Future<bool> createPackage({
    required String recipientName,
    required String recipientPhone,
    required String deliveryAddress,
    required String size,
    required String description,
    bool isFragile = false,
    String paymentMethod = 'cash',
  }) async {
    final currentState = state.valueOrNull ?? const PackageState();
    state = AsyncValue.data(currentState.copyWith(isCreating: true));

    try {
      final repo = ref.read(packageRepositoryProvider);
      final package = await repo.createPackage(
        recipientName: recipientName,
        recipientPhone: recipientPhone,
        deliveryAddress: deliveryAddress,
        size: size,
        description: description,
        isFragile: isFragile,
        paymentMethod: paymentMethod,
      );

      final updatedPackages = [package, ...currentState.myPackages];
      state = AsyncValue.data(PackageState.created(package).copyWith(
        myPackages: updatedPackages,
      ));
      return true;
    } catch (e) {
      state = AsyncValue.data(currentState.copyWith(
        isCreating: false,
        errorMessage: e.toString(),
      ));
      return false;
    }
  }

  /// Rastrea una encomienda.
  Future<void> trackPackage(String code) async {
    final currentState = state.valueOrNull ?? const PackageState();
    state = AsyncValue.data(currentState.copyWith(isTracking: true));

    try {
      final repo = ref.read(packageRepositoryProvider);
      final result = await repo.trackPackage(code);

      state = AsyncValue.data(PackageState.tracked(
        result['package'] as PackageModel,
        result['tracking_history'] as List<TrackingEventModel>,
      ));
    } catch (e) {
      state = AsyncValue.data(currentState.copyWith(
        isTracking: false,
        errorMessage: e.toString(),
      ));
    }
  }

  /// Carga las encomiendas del usuario.
  Future<void> loadMyPackages() async {
    final currentState = state.valueOrNull ?? const PackageState();
    state = AsyncValue.data(currentState.copyWith(isLoading: true));

    try {
      final repo = ref.read(packageRepositoryProvider);
      final packages = await repo.getMyPackages();
      state = AsyncValue.data(currentState.copyWith(
        myPackages: packages,
        isLoading: false,
      ));
    } catch (e) {
      state = AsyncValue.data(currentState.copyWith(isLoading: false));
    }
  }

  /// Limpia el tracking.
  void clearTracking() {
    final currentState = state.valueOrNull;
    if (currentState != null) {
      state = AsyncValue.data(PackageState(
        flowStatus: PackageFlowStatus.idle,
        myPackages: currentState.myPackages,
        currentPage: currentState.currentPage,
        hasMorePages: currentState.hasMorePages,
      ));
    }
  }

  /// Limpia errores.
  void clearError() {
    final currentState = state.valueOrNull;
    if (currentState != null) {
      state = AsyncValue.data(currentState.copyWith(errorMessage: null));
    }
  }
}