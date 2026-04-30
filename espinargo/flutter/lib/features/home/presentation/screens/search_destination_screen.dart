import 'dart:async';

import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../../../core/theme/app_colors.dart';
import '../../../../core/theme/app_text_styles.dart';
import '../../data/models/place_model.dart';
import '../../domain/providers/location_provider.dart';
import '../../domain/providers/map_provider.dart';
import '../widgets/place_search_tile.dart';

/// Pantalla de búsqueda de destino.
/// Aparece cuando el usuario toca la barra de búsqueda.
class SearchDestinationScreen extends ConsumerStatefulWidget {
  const SearchDestinationScreen({super.key});

  @override
  ConsumerState<SearchDestinationScreen> createState() => _SearchDestinationScreenState();
}

class _SearchDestinationScreenState extends ConsumerState<SearchDestinationScreen> {
  final TextEditingController _searchController = TextEditingController();
  final FocusNode _focusNode = FocusNode();
  Timer? _debounceTimer;

  @override
  void initState() {
    super.initState();
    // Enfocar automáticamente
    WidgetsBinding.instance.addPostFrameCallback((_) {
      _focusNode.requestFocus();
    });
  }

  @override
  void dispose() {
    _searchController.dispose();
    _focusNode.dispose();
    _debounceTimer?.cancel();
    super.dispose();
  }

  void _onSearchChanged(String query) {
    _debounceTimer?.cancel();
    _debounceTimer = Timer(const Duration(milliseconds: 500), () {
      _performSearch(query);
    });
  }

  Future<void> _performSearch(String query) async {
    final locationState = ref.read(locationProvider).valueOrNull;
    final userLocation = locationState?.currentLatLng;

    await ref.read(mapProvider.notifier).searchPlaces(query, userLocation: userLocation);
  }

  void _selectPlace(PlaceModel place) async {
    // Guardar en historial reciente (implementar después con SharedPreferences)
    await ref.read(mapProvider.notifier).setDestination(place);
    if (mounted) {
      Navigator.pop(context, place);
    }
  }

  @override
  Widget build(BuildContext context) {
    final mapState = ref.watch(mapProvider).valueOrNull;

    return Scaffold(
      backgroundColor: AppColors.background,
      appBar: AppBar(
        backgroundColor: Colors.transparent,
        elevation: 0,
        leading: IconButton(
          icon: const Icon(Icons.close, color: AppColors.textPrimary),
          onPressed: () => Navigator.pop(context),
        ),
        title: TextField(
          controller: _searchController,
          focusNode: _focusNode,
          onChanged: _onSearchChanged,
          decoration: InputDecoration(
            hintText: 'Busca tu destino en Espinar...',
            hintStyle: AppTextStyles.bodyMedium.copyWith(
              color: AppColors.textDisabled,
            ),
            border: InputBorder.none,
          ),
          style: AppTextStyles.bodyMedium,
        ),
        actions: [
          if (_searchController.text.isNotEmpty)
            IconButton(
              icon: const Icon(Icons.clear, color: AppColors.textSecondary),
              onPressed: () {
                _searchController.clear();
                ref.read(mapProvider.notifier).clearSearch();
              },
            ),
        ],
      ),
      body: _buildBody(mapState),
    );
  }

  Widget _buildBody(MapState? mapState) {
    // Mostrar resultados si hay búsqueda
    if (_searchController.text.isNotEmpty) {
      if (mapState?.isSearching ?? false) {
        return _buildLoadingResults();
      }

      final results = mapState?.searchResults ?? [];

      if (results.isEmpty) {
        return Center(
          child: Padding(
            padding: const EdgeInsets.all(24),
            child: Column(
              mainAxisAlignment: MainAxisAlignment.center,
              children: [
                const Icon(
                  Icons.search_off,
                  size: 64,
                  color: AppColors.textDisabled,
                ),
                const SizedBox(height: 16),
                Text(
                  'No se encontraron lugares para "${_searchController.text}" en Espinar',
                  textAlign: TextAlign.center,
                  style: AppTextStyles.bodyMedium.copyWith(
                    color: AppColors.textSecondary,
                  ),
                ),
              ],
            ),
          ),
        );
      }

      return ListView.separated(
        itemCount: results.length,
        separatorBuilder: (_, __) => const Divider(height: 1, indent: 52),
        itemBuilder: (context, index) {
          final place = results[index];
          return PlaceSearchTile(
            place: place,
            onTap: () => _selectPlace(place),
          );
        },
      );
    }

    // Lugares frecuentes cuando no hay búsqueda
    return _buildFrequentPlaces();
  }

  Widget _buildLoadingResults() {
    return ListView.builder(
      itemCount: 3,
      itemBuilder: (context, index) {
        return Container(
          padding: const EdgeInsets.all(16),
          child: Row(
            children: [
              Container(
                width: 24,
                height: 24,
                decoration: BoxDecoration(
                  color: AppColors.border,
                  borderRadius: BorderRadius.circular(12),
                ),
              ),
              const SizedBox(width: 12),
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Container(
                      height: 14,
                      width: double.infinity,
                      decoration: BoxDecoration(
                        color: AppColors.border,
                        borderRadius: BorderRadius.circular(4),
                      ),
                    ),
                    const SizedBox(height: 8),
                    Container(
                      height: 10,
                      width: 150,
                      decoration: BoxDecoration(
                        color: AppColors.border,
                        borderRadius: BorderRadius.circular(4),
                      ),
                    ),
                  ],
                ),
              ),
            ],
          ),
        );
      },
    );
  }

  Widget _buildFrequentPlaces() {
    return ListView(
      padding: const EdgeInsets.symmetric(vertical: 8),
      children: [
        _buildFrequentTile(
          icon: Icons.home_outlined,
          label: 'Mi casa',
          onTap: () {},
        ),
        _buildFrequentTile(
          icon: Icons.work_outline,
          label: 'Mi trabajo',
          onTap: () {},
        ),
      ],
    );
  }

  Widget _buildFrequentTile({
    required IconData icon,
    required String label,
    required VoidCallback onTap,
  }) {
    return ListTile(
      leading: Icon(icon, color: AppColors.primary),
      title: Text(label, style: AppTextStyles.bodyMedium),
      onTap: onTap,
      contentPadding: const EdgeInsets.symmetric(horizontal: 16, vertical: 4),
    );
  }
}