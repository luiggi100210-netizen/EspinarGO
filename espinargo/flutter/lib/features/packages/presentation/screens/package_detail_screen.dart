import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../../../core/theme/app_colors.dart';
import '../../../../core/theme/app_text_styles.dart';
import '../../../../shared/widgets/loading_indicator.dart';
import '../../data/models/package_model.dart';
import '../../data/models/tracking_event_model.dart';
import '../../domain/providers/package_provider.dart';
import '../widgets/tracking_timeline.dart';

/// Pantalla de detalle de una encomienda.
class PackageDetailScreen extends ConsumerWidget {
  final String trackingCode;

  const PackageDetailScreen({super.key, required this.trackingCode});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    return FutureBuilder<Map<String, dynamic>>(
      future: _loadData(ref, trackingCode),
      builder: (context, snapshot) {
        if (snapshot.connectionState == ConnectionState.waiting) {
          return const Scaffold(body: LoadingIndicator());
        }

        if (!snapshot.hasData) {
          return Scaffold(
            appBar: AppBar(title: const Text('Detalle')),
            body: const Center(child: Text('Encomienda no encontrada')),
          );
        }

        final package = snapshot.data!['package'] as PackageModel;
        final history = snapshot.data!['tracking_history'] as List<TrackingEventModel>;
        return Scaffold(
          appBar: AppBar(
            title: Text(package.trackingCode),
            actions: [
              IconButton(
                icon: const Icon(Icons.share),
                onPressed: () {},
              ),
            ],
          ),
          body: SingleChildScrollView(
            padding: const EdgeInsets.all(16),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                _buildHeader(package),
                const SizedBox(height: 24),
                _buildInfoSection(package),
                const SizedBox(height: 24),
                Text('Historial', style: AppTextStyles.labelLarge),
                const SizedBox(height: 12),
                TrackingTimeline(
                  events: history,
                  currentStatus: package.status,
                ),
              ],
            ),
          ),
        );
      },
    );
  }

  Future<Map<String, dynamic>> _loadData(WidgetRef ref, String code) async {
    final repo = ref.read(packageRepositoryProvider);
    return repo.trackPackage(code);
  }

  Widget _buildHeader(PackageModel package) {
    return Container(
      padding: const EdgeInsets.all(20),
      decoration: BoxDecoration(
        gradient: LinearGradient(
          colors: [AppColors.package, AppColors.packageLight],
          begin: Alignment.topLeft,
          end: Alignment.bottomRight,
        ),
        borderRadius: BorderRadius.circular(20),
      ),
      child: Row(
        children: [
          Text(package.sizeEmoji, style: const TextStyle(fontSize: 50)),
          const SizedBox(width: 16),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(package.sizeLabel, style: AppTextStyles.headingMedium.copyWith(color: Colors.white)),
                Text(package.statusLabel, style: AppTextStyles.bodyMedium.copyWith(color: Colors.white70)),
                const SizedBox(height: 4),
                Text(package.trackingCode, style: AppTextStyles.trackingCode.copyWith(color: Colors.white)),
              ],
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildInfoSection(PackageModel package) {
    return Container(
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(color: Colors.white, borderRadius: BorderRadius.circular(16)),
      child: Column(
        children: [
          _buildInfoRow('De', package.sender?.fullName ?? 'N/A', Icons.arrow_upward),
          const Divider(),
          _buildInfoRow('Para', package.recipientName, Icons.arrow_downward),
          const Divider(),
          _buildInfoRow('Dirección', package.deliveryAddress, Icons.location_on),
          const Divider(),
          _buildInfoRow('Descripción', package.description, Icons.inventory_2),
          const Divider(),
          _buildInfoRow('Precio', package.formattedPrice, Icons.attach_money),
          if (package.isFragile) ...[
            const Divider(),
            _buildInfoRow('Etiqueta', 'Frágil', Icons.warning, color: AppColors.error),
          ],
        ],
      ),
    );
  }

  Widget _buildInfoRow(String label, String value, IconData icon, {Color? color}) {
    return Padding(
      padding: const EdgeInsets.symmetric(vertical: 8),
      child: Row(
        children: [
          Icon(icon, size: 20, color: color ?? AppColors.textSecondary),
          const SizedBox(width: 12),
          Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Text(label, style: AppTextStyles.labelSmall),
              Text(value, style: AppTextStyles.bodyMedium),
            ],
          ),
        ],
      ),
    );
  }
}