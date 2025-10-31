import 'package:flutter/material.dart';
import 'models.dart';
import '../../routes/app_routes.dart';
import '../../widgets/app_footer_nav.dart';

class PackingResultsPage extends StatefulWidget {
  final PackingFormData form;
  const PackingResultsPage({super.key, required this.form});

  @override
  State<PackingResultsPage> createState() => _PackingResultsPageState();
}

class _PackingResultsPageState extends State<PackingResultsPage> {
  late List<PackingSection> sections;

  @override
  void initState() {
    super.initState();
    sections = _generateSections(widget.form);
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
              onTap: () {},
              tooltip: 'Export',
            ),
          ),
        ],
      ),
      body: ListView.builder(
        padding: const EdgeInsets.all(12),
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
                        .map((PackingItem it) => it.id == id ? it.copyWith(checked: value) : it)
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
                          .map((PackingItem it) => it.id == updated.id ? updated : it)
                          .toList(),
                    );
                  }).toList();
                });
              }
            },
          );
        },
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


