import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import '../../../../core/theme/app_colors.dart';
import '../../../../core/theme/app_text_styles.dart';
import '../../data/models/package_model.dart';
import '../widgets/tracking_search_bar.dart';
import '../widgets/tracking_timeline.dart';
import '../widgets/package_card.dart';
import '../../domain/providers/package_provider.dart';

/// Pantalla principal de rastreo de paquetes.
class TrackPackageScreen extends ConsumerStatefulWidget {
  final String? initialCode;

  const TrackPackageScreen({super.key, this.initialCode});

  @override
  ConsumerState<TrackPackageScreen> createState() => _TrackPackageScreenState();
}

class _TrackPackageScreenState extends ConsumerState<TrackPackageScreen> {
  @override
  void initState() {
    super.initState();
    if (widget.initialCode != null && widget.initialCode!.isNotEmpty) {
      WidgetsBinding.instance.addPostFrameCallback((_) {
        ref.read(packageProvider.notifier).trackPackage(widget.initialCode!);
      });
    }
  }

  @override
  Widget build(BuildContext context) {
    final state = ref.watch(packageProvider);
    final packageState = state.valueOrNull;

    return Scaffold(
      appBar: AppBar(
        title: const Text('Rastrear encomienda'),
        backgroundColor: Colors.transparent,
        actions: [
          IconButton(
            icon: const Icon(Icons.history),
            onPressed: () => context.push('/packages/history'),
          ),
        ],
      ),
      body: SingleChildScrollView(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            TrackingSearchBar(
              isLoading: packageState?.isTracking ?? false,
              initialValue: widget.initialCode,
              onSearch: (code) => ref.read(packageProvider.notifier).trackPackage(code),
            ),
            if (packageState?.trackedPackage != null) ...[
              const SizedBox(height: 24),
              _buildPackageInfo(packageState!.trackedPackage!),
              const SizedBox(height: 24),
              Text('Historial', style: AppTextStyles.labelLarge),
              const SizedBox(height: 12),
              TrackingTimeline(
                events: packageState.trackingHistory,
                currentStatus: packageState.trackedPackage!.status,
              ),
            ],
            if (packageState?.myPackages != null && packageState!.hasPackages) ...[
              const SizedBox(height: 32),
              Text('Mis encomiendas', style: AppTextStyles.labelLarge),
              const SizedBox(height: 12),
              ...packageState.myPackages.take(5).map((pkg) => PackageCard(
                    package: pkg,
                    onTap: () => context.push('/packages/detail/${pkg.trackingCode}'),
                  )),
              if (packageState.myPackages.length > 5)
                Center(
                  child: TextButton(
                    onPressed: () => context.push('/packages'),
                    child: Text('Ver todas (${packageState.myPackages.length})'),
                  ),
                ),
            ],
          ],
        ),
      ),
      floatingActionButton: FloatingActionButton.extended(
        onPressed: () => context.push('/packages/send'),
        icon: const Icon(Icons.add),
        label: const Text('Nueva'),
        backgroundColor: AppColors.package,
      ),
    );
  }

  Widget _buildPackageInfo(PackageModel package) {
    return Container(
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        color: Colors.white,
        borderRadius: BorderRadius.circular(16),
        border: Border.all(color: AppColors.package),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            children: [
              Text(package.sizeEmoji, style: const TextStyle(fontSize: 40)),
              const SizedBox(width: 16),
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(package.trackingCode, style: AppTextStyles.trackingCode),
                    Text(package.sizeLabel, style: AppTextStyles.bodyMedium),
                  ],
                ),
              ),
            ],
          ),
          const Divider(height: 24),
          Row(
            children: [
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text('Destinatario', style: AppTextStyles.labelSmall),
                    Text(package.recipientName, style: AppTextStyles.bodyMedium),
                  ],
                ),
              ),
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text('Estado', style: AppTextStyles.labelSmall),
                    Text(package.statusLabel, style: AppTextStyles.bodyMedium.copyWith(color: package.statusColor)),
                  ],
                ),
              ),
            ],
          ),
          const SizedBox(height: 12),
          Text('Dirección: ${package.deliveryAddress}', style: AppTextStyles.bodySmall),
        ],
      ),
    );
  }
}