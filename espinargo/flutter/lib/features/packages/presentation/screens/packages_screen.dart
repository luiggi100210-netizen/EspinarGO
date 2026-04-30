import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import '../../../../core/theme/app_colors.dart';
import '../../../../core/theme/app_text_styles.dart';
import '../../../../shared/widgets/loading_indicator.dart';
import '../../domain/providers/package_provider.dart';
import '../widgets/package_card.dart';

/// Pantalla de lista de encomiendas del usuario.
class PackagesScreen extends ConsumerWidget {
  const PackagesScreen({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final state = ref.watch(packageProvider);
    final packageState = state.valueOrNull;

    return Scaffold(
      appBar: AppBar(
        title: const Text('Mis encomiendas'),
        backgroundColor: Colors.transparent,
      ),
      body: packageState == null
          ? const LoadingIndicator()
          : packageState.myPackages.isEmpty
              ? _buildEmptyState(context)
              : _buildPackageList(context, packageState),
      floatingActionButton: FloatingActionButton.extended(
        onPressed: () => context.push('/packages/send'),
        icon: const Icon(Icons.add),
        label: const Text('Nueva'),
        backgroundColor: AppColors.package,
      ),
    );
  }

  Widget _buildEmptyState(BuildContext context) {
    return Center(
      child: Column(
        mainAxisAlignment: MainAxisAlignment.center,
        children: [
          const Icon(Icons.inventory_2_outlined, size: 80, color: AppColors.textDisabled),
          const SizedBox(height: 16),
          Text('No tienes encomiendas', style: AppTextStyles.headingSmall),
          const SizedBox(height: 8),
          Text('Crea tu primera encomienda', style: AppTextStyles.bodyMedium.copyWith(color: AppColors.textSecondary)),
          const SizedBox(height: 24),
          ElevatedButton.icon(
            onPressed: () => context.push('/packages/send'),
            icon: const Icon(Icons.add),
            label: const Text('Crear encomienda'),
          ),
        ],
      ),
    );
  }

  Widget _buildPackageList(BuildContext context, dynamic packageState) {
    return RefreshIndicator(
      onRefresh: () => ref.read(packageProvider.notifier).loadMyPackages(),
      child: ListView.builder(
        padding: const EdgeInsets.all(16),
        itemCount: packageState.myPackages.length,
        itemBuilder: (context, index) {
          final package = packageState.myPackages[index];
          return PackageCard(
            package: package,
            onTap: () => context.push('/packages/detail/${package.trackingCode}'),
          );
        },
      ),
    );
  }
}