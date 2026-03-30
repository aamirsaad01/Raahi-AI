import 'package:flutter/material.dart';
import 'models.dart';

class HazardDetailSheet extends StatelessWidget {
  final HazardReport report;
  const HazardDetailSheet({super.key, required this.report});

  @override
  Widget build(BuildContext context) {
    final TextTheme text = Theme.of(context).textTheme;
    final ColorScheme colors = Theme.of(context).colorScheme;
    
    return SingleChildScrollView(
      child: Padding(
        padding: const EdgeInsets.all(20.0),
      child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
        mainAxisSize: MainAxisSize.min,
          children: <Widget>[
            // Header with icon, title, and severity
            Row(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: <Widget>[
              Container(
                  padding: const EdgeInsets.all(12),
                decoration: BoxDecoration(
                  color: _colorFor(report.severity).withOpacity(0.15),
                    borderRadius: BorderRadius.circular(12),
                ),
                  child: Icon(
                    _iconFor(report.type),
                    color: _colorFor(report.severity),
                    size: 32,
                  ),
                ),
                const SizedBox(width: 16),
                Expanded(
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: <Widget>[
                      Text(
                        report.advisoryType ?? report.type.label,  // Use heading from model if available
                        style: text.titleLarge?.copyWith(
                          fontWeight: FontWeight.bold,
                        ),
                      ),
                      const SizedBox(height: 4),
                      Container(
                        padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 4),
                        decoration: BoxDecoration(
                          color: _colorFor(report.severity).withOpacity(0.2),
                          borderRadius: BorderRadius.circular(6),
                          border: Border.all(
                            color: _colorFor(report.severity),
                            width: 1.5,
                          ),
                        ),
                        child: Text(
                          report.severity.label.toUpperCase(),
                          style: TextStyle(
                            color: _colorFor(report.severity),
                            fontSize: 12,
                            fontWeight: FontWeight.bold,
                            letterSpacing: 0.5,
                          ),
                        ),
                      ),
                    ],
                  ),
              ),
            ],
          ),
            const SizedBox(height: 24),
            
            // Location Section
            _buildInfoSection(
              context: context,
              icon: Icons.location_on_rounded,
              iconColor: Colors.red,
              title: 'Location',
              content: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: <Widget>[
                  Text(
                    report.location,
                    style: text.bodyLarge?.copyWith(
                      fontWeight: FontWeight.w600,
                    ),
                  ),
                  if (report.lat != 0.0 && report.lon != 0.0) ...[
          const SizedBox(height: 4),
          Row(
            children: <Widget>[
                        Icon(Icons.map_rounded, size: 14, color: colors.onSurfaceVariant),
                        const SizedBox(width: 4),
                        Text(
                          '${report.lat.toStringAsFixed(6)}, ${report.lon.toStringAsFixed(6)}',
                          style: text.bodySmall?.copyWith(
                            color: colors.onSurfaceVariant,
                            fontFamily: 'monospace',
                          ),
                        ),
                      ],
                    ),
                  ],
                ],
              ),
            ),
            
            const SizedBox(height: 16),
            
            // Source Section
            _buildInfoSection(
              context: context,
              icon: Icons.source_rounded,
              iconColor: _getSourceColor(report.source),
              title: 'Source',
              content: _buildSourceChip(context, report.source, report.advisoryType),
            ),
            
            const SizedBox(height: 16),
            
            // Time Section
            _buildInfoSection(
              context: context,
              icon: Icons.access_time_rounded,
              iconColor: Colors.blue,
              title: 'Reported',
              content: Text(
                _formatTimestamp(report.timestamp),
                style: text.bodyMedium,
              ),
            ),
            
            // Description Section
            if (report.description != null && report.description!.isNotEmpty) ...[
              const SizedBox(height: 16),
              _buildInfoSection(
                context: context,
                icon: Icons.description_rounded,
                iconColor: Colors.purple,
                title: 'Description',
                content: Container(
                  padding: const EdgeInsets.all(12),
                  decoration: BoxDecoration(
                    color: colors.surfaceVariant.withOpacity(0.5),
                    borderRadius: BorderRadius.circular(8),
                    border: Border.all(color: colors.outline.withOpacity(0.2)),
                  ),
                  child: Text(
                    report.description!,
                    style: text.bodyMedium?.copyWith(
                      height: 1.5,
                    ),
                  ),
                ),
              ),
            ],
            
            // Advisory URL (if available)
            if (report.advisoryUrl != null && report.advisoryUrl!.isNotEmpty) ...[
              const SizedBox(height: 16),
              SizedBox(
                width: double.infinity,
                child: OutlinedButton.icon(
                  onPressed: () {
                    // TODO: Open URL in browser using url_launcher package
                    ScaffoldMessenger.of(context).showSnackBar(
                      SnackBar(
                        content: Text('Advisory URL: ${report.advisoryUrl}'),
                        action: SnackBarAction(
                          label: 'Copy',
                          onPressed: () {
                            // TODO: Copy to clipboard
                          },
                        ),
                      ),
                    );
                  },
                  icon: const Icon(Icons.open_in_new_rounded),
                  label: const Text('View Full Advisory'),
                  style: OutlinedButton.styleFrom(
                    padding: const EdgeInsets.symmetric(vertical: 12),
                  ),
                ),
              ),
            ],
            
            const SizedBox(height: 16),
            
            // Close button
            SizedBox(
              width: double.infinity,
              child: FilledButton(
                onPressed: () => Navigator.of(context).pop(),
                child: const Text('Close'),
              ),
            ),
            ],
        ),
      ),
    );
  }

  Widget _buildInfoSection({
    required BuildContext context,
    required IconData icon,
    required Color iconColor,
    required String title,
    required Widget content,
  }) {
    return Row(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: <Widget>[
        Container(
          padding: const EdgeInsets.all(8),
          decoration: BoxDecoration(
            color: iconColor.withOpacity(0.1),
            borderRadius: BorderRadius.circular(8),
          ),
          child: Icon(icon, size: 20, color: iconColor),
        ),
        const SizedBox(width: 12),
        Expanded(
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: <Widget>[
              Text(
                title,
                style: Theme.of(context).textTheme.labelMedium?.copyWith(
                  color: Theme.of(context).colorScheme.onSurfaceVariant,
                  fontWeight: FontWeight.w600,
                ),
              ),
              const SizedBox(height: 4),
              content,
        ],
      ),
        ),
      ],
    );
  }

  Widget _buildSourceChip(BuildContext context, String source, String? advisoryType) {
    final textTheme = Theme.of(context).textTheme;
    Color chipColor;
    IconData icon;
    String displayText;
    
    switch (source.toUpperCase()) {
      case 'NDMA':
        chipColor = Colors.blue;
        icon = Icons.gpp_good_rounded;
        displayText = 'NDMA';
        break;
      case 'PMD':
        chipColor = Colors.cyan;
        icon = Icons.cloud_rounded;
        displayText = 'PMD';
        break;
      case 'USER':
      case 'YOU':
        chipColor = Colors.orange;
        icon = Icons.people_rounded;
        displayText = 'Crowd-Sourced';
        break;
      default:
        chipColor = Colors.grey;
        icon = Icons.info_rounded;
        displayText = source;
    }
    
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: <Widget>[
        Container(
          padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 6),
          decoration: BoxDecoration(
            color: chipColor.withOpacity(0.1),
            borderRadius: BorderRadius.circular(8),
            border: Border.all(color: chipColor.withOpacity(0.3), width: 1.5),
          ),
          child: Row(
            mainAxisSize: MainAxisSize.min,
            children: <Widget>[
              Icon(icon, size: 18, color: chipColor),
              const SizedBox(width: 6),
              Text(
                displayText,
                style: TextStyle(
                  color: chipColor,
                  fontSize: 14,
                  fontWeight: FontWeight.bold,
                ),
              ),
            ],
          ),
        ),
        if (advisoryType != null && advisoryType.isNotEmpty) ...[
          const SizedBox(height: 6),
          Container(
            padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
            decoration: BoxDecoration(
              color: Colors.blue.withOpacity(0.1),
              borderRadius: BorderRadius.circular(6),
            ),
            child: Text(
              advisoryType,
              style: textTheme.bodySmall?.copyWith(
                color: Colors.blue.shade700,
                fontWeight: FontWeight.w500,
              ),
            ),
          ),
        ],
      ],
    );
  }

  Color _getSourceColor(String source) {
    switch (source.toUpperCase()) {
      case 'NDMA':
        return Colors.blue;
      case 'PMD':
        return Colors.cyan;
      case 'USER':
      case 'YOU':
        return Colors.orange;
      default:
        return Colors.grey;
    }
  }

  IconData _iconFor(HazardType t) {
    switch (t) {
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

  Color _colorFor(Severity s) {
    switch (s) {
      case Severity.low:
        return Colors.green; // Green for casual
      case Severity.medium:
        return Colors.orange; // Yellow/Orange for mild
      case Severity.high:
      case Severity.critical:
        return Colors.red; // Red for severe
    }
  }

  String _formatTimestamp(DateTime timestamp) {
    final now = DateTime.now();
    final difference = now.difference(timestamp);

    if (difference.inDays > 0) {
      return '${difference.inDays} day${difference.inDays > 1 ? 's' : ''} ago';
    } else if (difference.inHours > 0) {
      return '${difference.inHours} hour${difference.inHours > 1 ? 's' : ''} ago';
    } else if (difference.inMinutes > 0) {
      return '${difference.inMinutes} minute${difference.inMinutes > 1 ? 's' : ''} ago';
    } else {
      return 'Just now';
    }
  }
}


