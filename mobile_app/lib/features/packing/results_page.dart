import 'dart:io';
import 'package:flutter/material.dart';
import 'models.dart';
import '../../routes/app_routes.dart';
import '../../utils/app_constants.dart';
import '../../widgets/app_footer_nav.dart';
import 'api_service.dart';
import 'export_service.dart';

class PackingResultsPage extends StatefulWidget {
  final PackingFormData form;
  const PackingResultsPage({super.key, required this.form});

  @override
  State<PackingResultsPage> createState() => _PackingResultsPageState();
}

class _PackingResultsPageState extends State<PackingResultsPage> {
  late List<PackingSection> sections;
  bool isLoading = true;
  String? errorMessage;
  ChecklistMetadata? metadata;

  @override
  void initState() {
    super.initState();
    _loadChecklistFromBackend();
  }

  Future<void> _loadChecklistFromBackend() async {
    setState(() {
      isLoading = true;
      errorMessage = null;
    });

    try {
      final apiService = PackingApiService();
      
      // Convert activities to backend format
      final activities = widget.form.activities
          .map((a) => a.backendValue)
          .toList();

      final response = await apiService.generateChecklist(
        region: widget.form.region.label,
        area: widget.form.area,
        month: widget.form.month,
        activities: activities,
      );

      setState(() {
        sections = response.sections;
        metadata = response.metadata;
        isLoading = false;
      });
    } catch (e) {
      setState(() {
        errorMessage = e.toString();
        isLoading = false;
        // Fallback to empty sections
        sections = [];
      });
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('Your Checklist'),
        actions: <Widget>[
          Padding(
            padding: const EdgeInsets.only(right: 8.0),
            child: _IconFilledButton(
              icon: Icons.save_outlined,
              onTap: () {},
              tooltip: 'Save',
            ),
          ),
          Padding(
            padding: const EdgeInsets.only(right: 8.0),
            child: _IconFilledButton(
              icon: Icons.ios_share_rounded,
              onTap: () => _showExportOptions(context),  // UPDATED
              tooltip: 'Export',
            ),
          ),
        ],
      ),
      body: isLoading
          ? const Center(child: CircularProgressIndicator())
          : errorMessage != null
              ? _ErrorView(
                  message: errorMessage!,
                  onRetry: _loadChecklistFromBackend,
                )
              : Column(
                  children: [
                    // Show warnings/tips if available
                    if (metadata != null) _MetadataHeader(metadata: metadata!),
                    Expanded(
                      child: ListView.builder(
                        padding: const EdgeInsets.all(12).add(AppConstants.footerPadding),
                        itemCount: sections.length,
                        itemBuilder: (BuildContext context, int index) {
                          final PackingSection section = sections[index];
                          return _SectionCard(
                            section: section,
                            onItemToggle: (String id, bool value) {
                              setState(() {
                                sections = sections.map((PackingSection s) {
                                  if (s.title != section.title) return s;
                                  return PackingSection(
                                    title: s.title,
                                    items: s.items
                                        .map((PackingItem it) =>
                                            it.id == id ? it.copyWith(checked: value) : it)
                                        .toList(),
                                  );
                                }).toList();
                              });
                            },
                            onItemTap: (PackingItem item) async {
                              final PackingItem? updated = await Navigator.of(context).pushNamed(
                                AppRoutes.packingEdit,
                                arguments: item,
                              ) as PackingItem?;
                              if (updated != null) {
                                setState(() {
                                  sections = sections.map((PackingSection s) {
                                    if (s.title != section.title) return s;
                                    return PackingSection(
                                      title: s.title,
                                      items: s.items
                                          .map((PackingItem it) =>
                                              it.id == updated.id ? updated : it)
                                          .toList(),
                                    );
                                  }).toList();
                                });
                              }
                            },
                          );
                        },
                      ),
                    ),
                  ],
                ),
    );
  }

  // ADD THIS METHOD inside _PackingResultsPageState class
  void _showExportOptions(BuildContext context) {
    showModalBottomSheet(
      context: context,
      builder: (BuildContext context) {
        return SafeArea(
          child: Column(
            mainAxisSize: MainAxisSize.min,
            children: [
              ListTile(
                leading: const Icon(Icons.description_outlined),
                title: const Text('Export as Text File'),
                subtitle: const Text('Simple text format with checkboxes'),
                onTap: () {
                  Navigator.pop(context);
                  _exportAsText();
                },
              ),
              ListTile(
                leading: const Icon(Icons.table_chart_outlined),
                title: const Text('Export as CSV'),
                subtitle: const Text('Spreadsheet format for Excel'),
                onTap: () {
                  Navigator.pop(context);
                  _exportAsCSV();
                },
              ),
              ListTile(
                leading: const Icon(Icons.code_outlined),
                title: const Text('Export as Markdown'),
                subtitle: const Text('Formatted document with checkboxes'),
                onTap: () {
                  Navigator.pop(context);
                  _exportAsMarkdown();
                },
              ),
              const SizedBox(height: 8),
            ],
          ),
        );
      },
    );
  }

  // ADD THIS METHOD
  Future<void> _exportAsText() async {
    try {
      await ChecklistExportService.exportAsText(
        sections: sections,
        destination: widget.form.area,
        month: widget.form.month.toString(),
      );
      
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(content: Text('Checklist exported successfully!')),
        );
      }
    } catch (e) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text('Export failed: $e')),
        );
      }
    }
  }

  // ADD THIS METHOD
  Future<void> _exportAsCSV() async {
    try {
      await ChecklistExportService.exportAsCSV(
        sections: sections,
        destination: widget.form.area,
        month: widget.form.month.toString(),
      );
      
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(content: Text('Checklist exported as CSV!')),
        );
      }
    } catch (e) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text('Export failed: $e')),
        );
      }
    }
  }

  // ADD THIS METHOD
  Future<void> _exportAsMarkdown() async {
    try {
      await ChecklistExportService.exportAsMarkdown(
        sections: sections,
        destination: widget.form.area,
        month: widget.form.month.toString(),
      );
      
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(content: Text('Checklist exported as Markdown!')),
        );
      }
    } catch (e) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text('Export failed: $e')),
        );
      }
    }
  }
}

// ADD THIS: Error view widget
class _ErrorView extends StatelessWidget {
  final String message;
  final VoidCallback onRetry;

  const _ErrorView({required this.message, required this.onRetry});

  @override
  Widget build(BuildContext context) {
    return Center(
      child: Padding(
        padding: const EdgeInsets.all(24.0),
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            const Icon(Icons.error_outline, size: 64, color: Colors.red),
            const SizedBox(height: 16),
            Text(
              'Failed to generate checklist',
              style: Theme.of(context).textTheme.titleLarge,
            ),
            const SizedBox(height: 8),
            Text(
              message,
              textAlign: TextAlign.center,
              style: Theme.of(context).textTheme.bodyMedium,
            ),
            const SizedBox(height: 24),
            FilledButton.icon(
              onPressed: onRetry,
              icon: const Icon(Icons.refresh),
              label: const Text('Retry'),
            ),
          ],
        ),
      ),
    );
  }
}

// ADD THIS: Metadata header widget
class _MetadataHeader extends StatelessWidget {
  final ChecklistMetadata metadata;

  const _MetadataHeader({required this.metadata});

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    
    if (metadata.warnings.isEmpty && metadata.tips.isEmpty) {
      return const SizedBox.shrink();
    }

    return Card(
      margin: const EdgeInsets.all(12),
      child: Padding(
        padding: const EdgeInsets.all(16.0),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            if (metadata.warnings.isNotEmpty) ...[
              Row(
                children: [
                  const Icon(Icons.warning_amber_rounded, color: Colors.orange),
                  const SizedBox(width: 8),
                  Text('Important Warnings', style: theme.textTheme.titleMedium),
                ],
              ),
              const SizedBox(height: 8),
              ...metadata.warnings.map((w) => Padding(
                    padding: const EdgeInsets.only(left: 32, bottom: 4),
                    child: Text(w, style: theme.textTheme.bodySmall),
                  )),
              const SizedBox(height: 12),
            ],
            if (metadata.tips.isNotEmpty) ...[
              Row(
                children: [
                  const Icon(Icons.lightbulb_outline, color: Colors.blue),
                  const SizedBox(width: 8),
                  Text('Helpful Tips', style: theme.textTheme.titleMedium),
                ],
              ),
              const SizedBox(height: 8),
              ...metadata.tips.map((t) => Padding(
                    padding: const EdgeInsets.only(left: 32, bottom: 4),
                    child: Text(t, style: theme.textTheme.bodySmall),
                  )),
            ],
          ],
        ),
      ),
    );
  }
}

class _SectionCard extends StatelessWidget {
  final PackingSection section;
  final void Function(String id, bool value) onItemToggle;
  final void Function(PackingItem item) onItemTap;

  const _SectionCard({
    required this.section,
    required this.onItemToggle,
    required this.onItemTap,
  });

  @override
  Widget build(BuildContext context) {
    final ColorScheme colors = Theme.of(context).colorScheme;
    return Card(
      margin: const EdgeInsets.symmetric(vertical: 8),
      child: Padding(
        padding: const EdgeInsets.all(8.0),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: <Widget>[
            Padding(
              padding: const EdgeInsets.symmetric(horizontal: 8.0, vertical: 6.0),
              child: Text(section.title, style: Theme.of(context).textTheme.titleMedium),
            ),
            ...section.items.map((PackingItem item) => ListTile(
                  leading: Checkbox(
                    value: item.checked,
                    onChanged: (bool? v) => onItemToggle(item.id, v ?? false),
                  ),
                  title: Text(item.name),
                  subtitle: item.notes != null ? Text(item.notes!) : null,
                  trailing: Container(
                    padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
                    decoration: BoxDecoration(
                      color: colors.surfaceVariant,
                      borderRadius: BorderRadius.circular(8),
                    ),
                    child: Text('x${item.quantity}'),
                  ),
                  onTap: () => onItemTap(item),
                )),
          ],
        ),
      ),
    );
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
    if (tooltip != null) {
      return Tooltip(message: tooltip!, child: btn);
    }
    return btn;
  }
}

List<PackingSection> _generateSections(PackingFormData form) {
  // Placeholder deterministic content; later this will come from backend.
  final List<PackingItem> clothes = <PackingItem>[
    const PackingItem(id: 'shirt', name: 'Shirts', quantity: 3),
    const PackingItem(id: 'pant', name: 'Pants/Jeans', quantity: 2),
    const PackingItem(id: 'jacket', name: 'Jacket', quantity: 1),
  ];
  final List<PackingItem> meds = <PackingItem>[
    const PackingItem(id: 'firstaid', name: 'First Aid Kit'),
    const PackingItem(id: 'painkiller', name: 'Painkillers'),
  ];
  final List<PackingItem> gear = <PackingItem>[
    const PackingItem(id: 'bottle', name: 'Water Bottle'),
    const PackingItem(id: 'powerbank', name: 'Power Bank'),
    if (form.activities.contains(Activity.camping))
      const PackingItem(id: 'tent', name: 'Tent'),
  ];
  return <PackingSection>[
    const PackingSection(title: 'Clothes', items: <PackingItem>[]),
    const PackingSection(title: 'Medicines', items: <PackingItem>[]),
    const PackingSection(title: 'Gear', items: <PackingItem>[]),
  ].map((PackingSection s) {
    if (s.title == 'Clothes') return PackingSection(title: s.title, items: clothes);
    if (s.title == 'Medicines') return PackingSection(title: s.title, items: meds);
    return PackingSection(title: s.title, items: gear);
  }).toList();
}


