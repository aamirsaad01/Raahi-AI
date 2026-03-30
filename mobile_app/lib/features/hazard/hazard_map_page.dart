// import 'dart:developer' as developer;  // Not used after commenting out poller refresh
import 'package:flutter/material.dart';
import '../../routes/app_routes.dart';
import '../../utils/app_constants.dart';
import 'models.dart';
import 'hazard_detail_sheet.dart';
import 'layers_filters_sheet.dart';
import 'api_service.dart';

class HazardMapPage extends StatefulWidget {
  const HazardMapPage({super.key});

  @override
  State<HazardMapPage> createState() => _HazardMapPageState();
}

class _HazardMapPageState extends State<HazardMapPage> {
  final HazardApiService _apiService = HazardApiService();
  List<HazardReport> _hazards = [];
  bool _isLoading = true;
  String? _errorMessage;
  
  // Filter state
  String? _sourceFilter; // null = all, 'ndma', 'user', 'pmd'
  String? _severityFilter;
  String _timeWindow = 'all'; // '24h', '7d', '1m', 'all'

  @override
  void initState() {
    super.initState();
    _loadHazards();
  }

  Future<void> _loadHazards({bool refreshFromSource = false}) async {
    setState(() {
      _isLoading = true;
      _errorMessage = null;
    });

    try {
      // If refresh button was pressed, trigger scraper first
      // DISABLED: Poller should be run manually in separate terminal
      // if (refreshFromSource) {
      //   try {
      //     final refreshResult = await _apiService.refreshHazards();
      //     if (refreshResult['success'] == true) {
      //       final newCount = refreshResult['new_advisories'] ?? 0;
      //       if (newCount > 0 && mounted) {
      //         ScaffoldMessenger.of(context).showSnackBar(
      //           SnackBar(
      //             content: Text('✅ Found $newCount new advisories'),
      //             backgroundColor: Colors.green,
      //             duration: const Duration(seconds: 2),
      //           ),
      //         );
      //       }
      //     }
      //   } catch (e) {
      //     // If refresh fails, still try to load existing hazards
      //     developer.log('Refresh failed, loading existing hazards: $e');
      //     if (mounted) {
      //       ScaffoldMessenger.of(context).showSnackBar(
      //         SnackBar(
      //           content: Text('⚠️ Could not refresh: ${e.toString()}'),
      //           backgroundColor: Colors.orange,
      //           duration: const Duration(seconds: 2),
      //         ),
      //       );
      //     }
      //   }
      // }

      // Load hazards from database
      final hazards = await _apiService.getHazards(
        source: _sourceFilter,
        severity: _severityFilter,
        timeWindow: _timeWindow,
      );
      
      if (mounted) {
        setState(() {
          _hazards = hazards;
          _isLoading = false;
        });
      }
    } catch (e) {
      if (mounted) {
        setState(() {
          _errorMessage = e.toString();
          _isLoading = false;
          _hazards = [];
        });
      }
    }
  }

  void _applyFilters(String? source, String? severity, String timeWindow) {
    setState(() {
      _sourceFilter = source;
      _severityFilter = severity;
      _timeWindow = timeWindow;
    });
    _loadHazards();
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('Hazard Map'),
        actions: <Widget>[
          Padding(
            padding: const EdgeInsets.only(right: 8.0),
            child: _IconFilledButton(
              icon: Icons.layers_rounded,
              tooltip: 'Layers & Filters',
              onTap: () => showModalBottomSheet<void>(
                context: context,
                useSafeArea: true,
                showDragHandle: true,
                isScrollControlled: true,
                builder: (_) => LayersFiltersSheet(
                  onApply: _applyFilters,
                  initialSource: _sourceFilter,
                  initialSeverity: _severityFilter,
                  initialTimeWindow: _timeWindow,
                ),
              ),
            ),
          ),
          Padding(
            padding: const EdgeInsets.only(right: 8.0),
            child: _IconFilledButton(
              icon: Icons.bookmark_rounded,
              tooltip: 'My Reports',
              onTap: () => Navigator.of(context).pushNamed(AppRoutes.hazardMyReports),
            ),
          ),
          Padding(
            padding: const EdgeInsets.only(right: 8.0),
            child: _IconFilledButton(
              icon: Icons.refresh_rounded,
              tooltip: 'Refresh & Update',
              onTap: () => _loadHazards(refreshFromSource: true),
            ),
          ),
        ],
      ),
      floatingActionButton: SafeArea(
        minimum: const EdgeInsets.only(bottom: 60),
        child: FloatingActionButton.extended(
          onPressed: () async {
            final result = await Navigator.of(context).pushNamed(AppRoutes.hazardReport);
            if (result == true) {
              // Reload if a new hazard was reported
              _loadHazards();
            }
          },
          icon: const Icon(Icons.add_location_alt_rounded),
          label: const Text('Report'),
        ),
      ),
      body: _buildBody(),
    );
  }

  Widget _buildBody() {
    if (_isLoading) {
      return const Center(
        child: CircularProgressIndicator(),
      );
    }

    if (_errorMessage != null) {
      return Center(
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: <Widget>[
            Icon(Icons.error_outline, size: 64, color: Colors.red.shade300),
            const SizedBox(height: 16),
            Text(
              'Error loading hazards',
              style: Theme.of(context).textTheme.titleMedium,
            ),
            const SizedBox(height: 8),
            Padding(
              padding: const EdgeInsets.symmetric(horizontal: 32),
              child: Text(
                _errorMessage!,
                textAlign: TextAlign.center,
                style: Theme.of(context).textTheme.bodySmall,
              ),
            ),
            const SizedBox(height: 16),
            FilledButton.icon(
              onPressed: _loadHazards,
              icon: const Icon(Icons.refresh_rounded),
              label: const Text('Retry'),
            ),
          ],
        ),
      );
    }

    if (_hazards.isEmpty) {
      return Center(
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: <Widget>[
            Icon(Icons.location_off_rounded, size: 64, color: Colors.grey.shade400),
            const SizedBox(height: 16),
            Text(
              'No hazards found',
              style: Theme.of(context).textTheme.titleMedium,
            ),
            const SizedBox(height: 8),
            Padding(
              padding: const EdgeInsets.symmetric(horizontal: 32),
              child: Text(
                'No hazards match your current filters. Try:\n\n• Clicking the refresh button (↻) to fetch latest NDMA advisories\n• Adjusting your filters in the layers menu\n• Reporting a hazard using the + button',
                textAlign: TextAlign.center,
                style: Theme.of(context).textTheme.bodySmall,
              ),
            ),
            const SizedBox(height: 24),
            Row(
              mainAxisAlignment: MainAxisAlignment.center,
              children: <Widget>[
                FilledButton.icon(
                  onPressed: () => _loadHazards(refreshFromSource: true),
                  icon: const Icon(Icons.refresh_rounded),
                  label: const Text('Refresh from NDMA'),
                ),
                const SizedBox(width: 12),
                OutlinedButton.icon(
                  onPressed: _loadHazards,
                  icon: const Icon(Icons.filter_list_rounded),
                  label: const Text('Reload'),
                ),
              ],
            ),
          ],
        ),
      );
    }

    return RefreshIndicator(
      onRefresh: () => _loadHazards(refreshFromSource: true),
      child: ListView.separated(
        padding: const EdgeInsets.all(12).add(AppConstants.footerPadding),
        itemCount: _hazards.length,
        separatorBuilder: (_, __) => const SizedBox(height: 8),
        itemBuilder: (BuildContext context, int i) {
          final HazardReport r = _hazards[i];
          return Card(
            elevation: 2,
            margin: EdgeInsets.zero,
            child: InkWell(
              onTap: () => showModalBottomSheet<void>(
                context: context,
                useSafeArea: true,
                showDragHandle: true,
                isScrollControlled: true,
                builder: (_) => HazardDetailSheet(report: r),
              ),
              child: Padding(
                padding: const EdgeInsets.all(12.0),
                child: Row(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: <Widget>[
                    // Icon with severity color
                    Container(
                      padding: const EdgeInsets.all(8),
                      decoration: BoxDecoration(
                        color: _colorFor(r.severity).withOpacity(0.1),
                        borderRadius: BorderRadius.circular(8),
                      ),
                      child: Icon(
                        _iconFor(r.type),
                        color: _colorFor(r.severity),
                        size: 24,
                      ),
                    ),
                    const SizedBox(width: 12),
                    // Content
                    Expanded(
                      child: Column(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: <Widget>[
                          // Title and severity badge
                          Row(
                            children: <Widget>[
                              Expanded(
                                child: Text(
                                  r.advisoryType ?? r.type.label,  // Use heading from model if available
                                  style: Theme.of(context).textTheme.titleMedium?.copyWith(
                                    fontWeight: FontWeight.bold,
                                  ),
                                ),
                              ),
                              Container(
                                padding: const EdgeInsets.symmetric(horizontal: 6, vertical: 2),
                                decoration: BoxDecoration(
                                  color: _colorFor(r.severity).withOpacity(0.15),
                                  borderRadius: BorderRadius.circular(4),
                                ),
                                child: Text(
                                  r.severity.label.toUpperCase(),
                                  style: TextStyle(
                                    color: _colorFor(r.severity),
                                    fontSize: 10,
                                    fontWeight: FontWeight.bold,
                                  ),
                                ),
                              ),
                            ],
                          ),
                          const SizedBox(height: 4),
                          // Location
                          Row(
                            children: <Widget>[
                              Icon(Icons.location_on_rounded, size: 14, color: Colors.grey.shade600),
                              const SizedBox(width: 4),
                              Expanded(
                                child: Text(
                                  r.location,
                                  style: Theme.of(context).textTheme.bodyMedium,
                                ),
                              ),
                            ],
                          ),
                          // Coordinates
                          if (r.lat != 0.0 && r.lon != 0.0) ...[
                            const SizedBox(height: 2),
                            Row(
                              children: <Widget>[
                                Icon(Icons.map_rounded, size: 12, color: Colors.grey.shade500),
                                const SizedBox(width: 4),
                                Text(
                                  '${r.lat.toStringAsFixed(4)}, ${r.lon.toStringAsFixed(4)}',
                                  style: Theme.of(context).textTheme.bodySmall?.copyWith(
                                    color: Colors.grey.shade600,
                                  ),
                                ),
                              ],
                            ),
                          ],
                          const SizedBox(height: 4),
                          // Source and time
                          Row(
                            children: <Widget>[
                              _buildSourceChip(r.source),
                              const SizedBox(width: 8),
                              Icon(Icons.access_time_rounded, size: 12, color: Colors.grey.shade500),
                              const SizedBox(width: 4),
                              Text(
                                _formatTimestamp(r.timestamp),
                                style: Theme.of(context).textTheme.bodySmall?.copyWith(
                                  color: Colors.grey.shade600,
                                ),
                              ),
                            ],
                          ),
                        ],
                      ),
                    ),
                    const SizedBox(width: 8),
                    Icon(Icons.chevron_right, color: Colors.grey.shade400),
                  ],
                ),
              ),
            ),
          );
        },
      ),
    );
  }

  String _formatTimestamp(DateTime timestamp) {
    final now = DateTime.now();
    final difference = now.difference(timestamp);

    if (difference.inDays > 0) {
      return '${difference.inDays}d ago';
    } else if (difference.inHours > 0) {
      return '${difference.inHours}h ago';
    } else if (difference.inMinutes > 0) {
      return '${difference.inMinutes}m ago';
    } else {
      return 'Just now';
    }
  }

  Widget _buildSourceChip(String source) {
    Color chipColor;
    IconData icon;
    
    switch (source.toUpperCase()) {
      case 'NDMA':
        chipColor = Colors.blue;
        icon = Icons.gpp_good_rounded;
        break;
      case 'PMD':
        chipColor = Colors.cyan;
        icon = Icons.cloud_rounded;
        break;
      case 'USER':
      case 'YOU':
        chipColor = Colors.orange;
        icon = Icons.people_rounded;
        break;
      default:
        chipColor = Colors.grey;
        icon = Icons.info_rounded;
    }
    
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 6, vertical: 2),
      decoration: BoxDecoration(
        color: chipColor.withOpacity(0.1),
        borderRadius: BorderRadius.circular(4),
        border: Border.all(color: chipColor.withOpacity(0.3), width: 1),
      ),
      child: Row(
        mainAxisSize: MainAxisSize.min,
        children: <Widget>[
          Icon(icon, size: 12, color: chipColor),
          const SizedBox(width: 4),
          Text(
            source == 'You' ? 'Crowd-Sourced' : source,
            style: TextStyle(
              color: chipColor,
              fontSize: 11,
              fontWeight: FontWeight.w600,
            ),
          ),
        ],
      ),
    );
  }

  IconData _iconFor(HazardType type) {
    switch (type) {
      case HazardType.landslide:
        return Icons.terrain_rounded;
      case HazardType.flood:
        return Icons.water_damage_rounded;
      case HazardType.roadblock:
        return Icons.block_rounded;
      case HazardType.snowfall:
        return Icons.ac_unit_rounded;
      case HazardType.protest:
        return Icons.groups_2_rounded;
      case HazardType.accident:
        return Icons.local_hospital_rounded;
    }
  }

  Color _colorFor(Severity severity) {
    switch (severity) {
      case Severity.low:
        return Colors.green; // Green for casual
      case Severity.medium:
        return Colors.orange; // Yellow/Orange for mild
      case Severity.high:
      case Severity.critical:
        return Colors.red; // Red for severe
    }
  }
}

class _IconFilledButton extends StatelessWidget {
  final IconData icon;
  final VoidCallback onTap;
  final String? tooltip;

  const _IconFilledButton({required this.icon, required this.onTap, this.tooltip});

  @override
  Widget build(BuildContext context) {
    final ColorScheme colors = Theme.of(context).colorScheme;
    final Widget btn = Material(
      color: colors.primary,
      shape: const StadiumBorder(),
      child: InkWell(
        customBorder: const StadiumBorder(),
        onTap: onTap,
        child: Padding(
          padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 8),
          child: Icon(icon, color: Colors.white),
        ),
      ),
    );
    if (tooltip != null) return Tooltip(message: tooltip!, child: btn);
    return btn;
  }
}


