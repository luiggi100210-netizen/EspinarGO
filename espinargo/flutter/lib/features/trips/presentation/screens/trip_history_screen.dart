import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../../../core/theme/app_colors.dart';
import '../../../../core/theme/app_text_styles.dart';
import '../../domain/providers/trip_provider.dart';
import '../widgets/trip_info_card.dart';

/// Historial de viajes del usuario.
class TripHistoryScreen extends ConsumerStatefulWidget {
  const TripHistoryScreen({super.key});

  @override
  ConsumerState<TripHistoryScreen> createState() => _TripHistoryScreenState();
}

class _TripHistoryScreenState extends ConsumerState<TripHistoryScreen> {
  @override
  void initState() {
    super.initState();
    // Cargar historial al abrir
    WidgetsBinding.instance.addPostFrameCallback((_) {
      ref.read(tripProvider.notifier).loadTripHistory();
    });
  }

  @override
  Widget build(BuildContext context) {
    final tripState = ref.watch(tripProvider).valueOrNull;
    final history = tripState?.tripHistory ?? [];
    final isLoading = tripState?.isLoadingHistory ?? false;

    return Scaffold(
      appBar: AppBar(
        title: const Text('Mis viajes'),
        backgroundColor: Colors.transparent,
        elevation: 0,
      ),
      body: isLoading
          ? const Center(child: CircularProgressIndicator())
          : history.isEmpty
              ? _buildEmptyState()
              : RefreshIndicator(
                  onRefresh: () async {
                    await ref.read(tripProvider.notifier).loadTripHistory();
                  },
                  child: ListView.builder(
                    padding: const EdgeInsets.all(16),
                    itemCount: history.length,
                    itemBuilder: (context, index) {
                      final trip = history[index];
                      return _buildTripItem(trip);
                    },
                  ),
                ),
    );
  }

  Widget _buildEmptyState() {
    return Center(
      child: Column(
        mainAxisAlignment: MainAxisAlignment.center,
        children: [
          const Text('🚗', style: TextStyle(fontSize: 64)),
          const SizedBox(height: 16),
          Text(
            'Aún no tienes viajes',
            style: AppTextStyles.headingMedium,
          ),
          const SizedBox(height: 8),
          Text(
            'Tu historial de viajes aparecerá aquí',
            style: AppTextStyles.bodyMedium.copyWith(
              color: AppColors.textSecondary,
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildTripItem(trip) {
    return Container(
      margin: const EdgeInsets.only(bottom: 12),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          // Fecha y estado
          Row(
            mainAxisAlignment: MainAxisAlignment.spaceBetween,
            children: [
              Text(
                _formatDate(trip.createdAt),
                style: AppTextStyles.labelMedium,
              ),
              _buildStatusBadge(trip.status),
            ],
          ),
          const SizedBox(height: 8),
          // Info del viaje
          TripInfoCard(trip: trip),
        ],
      ),
    );
  }

  Widget _buildStatusBadge(String status) {
    Color color;
    String text;

    switch (status) {
      case 'completed':
        color = AppColors.success;
        text = 'Completado';
        break;
      case 'cancelled':
        color = AppColors.error;
        text = 'Cancelado';
        break;
      default:
        color = AppColors.warning;
        text = status;
    }

    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
      decoration: BoxDecoration(
        color: color.withOpacity(0.1),
        borderRadius: BorderRadius.circular(8),
      ),
      child: Text(
        text,
        style: AppTextStyles.labelSmall.copyWith(color: color),
      ),
    );
  }

  String _formatDate(String dateStr) {
    try {
      final date = DateTime.parse(dateStr);
      return '${date.day}/${date.month}/${date.year}';
    } catch (_) {
      return dateStr;
    }
  }
}