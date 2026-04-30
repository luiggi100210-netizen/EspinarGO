import '../../data/models/package_model.dart';
import '../../data/models/tracking_event_model.dart';

/// Estado del módulo de encomiendas.
enum PackageFlowStatus {
  idle,
  creating,
  created,
  tracking,
  tracked,
  loading,
  error,
}

/// Estado inmutable del módulo de encomiendas.
class PackageState {
  final PackageFlowStatus flowStatus;
  final List<PackageModel> myPackages;
  final PackageModel? trackedPackage;
  final List<TrackingEventModel> trackingHistory;
  final PackageModel? lastCreatedPackage;
  final bool isLoading;
  final bool isCreating;
  final bool isTracking;
  final String? errorMessage;
  final int currentPage;
  final bool hasMorePages;

  const PackageState({
    this.flowStatus = PackageFlowStatus.idle,
    this.myPackages = const [],
    this.trackedPackage,
    this.trackingHistory = const [],
    this.lastCreatedPackage,
    this.isLoading = false,
    this.isCreating = false,
    this.isTracking = false,
    this.errorMessage,
    this.currentPage = 1,
    this.hasMorePages = true,
  });

  PackageState copyWith({
    PackageFlowStatus? flowStatus,
    List<PackageModel>? myPackages,
    PackageModel? trackedPackage,
    List<TrackingEventModel>? trackingHistory,
    PackageModel? lastCreatedPackage,
    bool? isLoading,
    bool? isCreating,
    bool? isTracking,
    String? errorMessage,
    int? currentPage,
    bool? hasMorePages,
  }) {
    return PackageState(
      flowStatus: flowStatus ?? this.flowStatus,
      myPackages: myPackages ?? this.myPackages,
      trackedPackage: trackedPackage ?? this.trackedPackage,
      trackingHistory: trackingHistory ?? this.trackingHistory,
      lastCreatedPackage: lastCreatedPackage ?? this.lastCreatedPackage,
      isLoading: isLoading ?? this.isLoading,
      isCreating: isCreating ?? this.isCreating,
      isTracking: isTracking ?? this.isTracking,
      errorMessage: errorMessage,
      currentPage: currentPage ?? this.currentPage,
      hasMorePages: hasMorePages ?? this.hasMorePages,
    );
  }

  factory PackageState.initial() => const PackageState(isLoading: true);
  factory PackageState.loading() => const PackageState(isLoading: true);
  factory PackageState.error(String message) => PackageState(
        flowStatus: PackageFlowStatus.error,
        errorMessage: message,
      );
  factory PackageState.created(PackageModel package) => PackageState(
        flowStatus: PackageFlowStatus.created,
        lastCreatedPackage: package,
      );
  factory PackageState.tracked(PackageModel package, List<TrackingEventModel> history) =>
      PackageState(
        flowStatus: PackageFlowStatus.tracked,
        trackedPackage: package,
        trackingHistory: history,
      );

  bool get hasPackages => myPackages.isNotEmpty;
  bool get hasTrackedResult => trackedPackage != null;
}