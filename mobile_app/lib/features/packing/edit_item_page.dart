import 'package:flutter/material.dart';
import 'models.dart';
import '../../widgets/app_footer_nav.dart';

class PackingEditItemPage extends StatefulWidget {
  final PackingItem item;
  const PackingEditItemPage({super.key, required this.item});

  @override
  State<PackingEditItemPage> createState() => _PackingEditItemPageState();
}

class _PackingEditItemPageState extends State<PackingEditItemPage> {
  late TextEditingController _name;
  late TextEditingController _notes;
  int _qty = 1;

  @override
  void initState() {
    super.initState();
    _name = TextEditingController(text: widget.item.name);
    _notes = TextEditingController(text: widget.item.notes ?? '');
    _qty = widget.item.quantity;
  }

  @override
  void dispose() {
    _name.dispose();
    _notes.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('Edit Item')),
      body: Padding(
        padding: const EdgeInsets.all(16.0),
        child: Column(
          children: <Widget>[
            TextField(
              controller: _name,
              decoration: const InputDecoration(labelText: 'Name', border: OutlineInputBorder()),
            ),
            const SizedBox(height: 12),
            Row(
              children: <Widget>[
                const Text('Quantity'),
                const SizedBox(width: 12),
                IconButton(
                  onPressed: _qty > 1 ? () => setState(() => _qty--) : null,
                  icon: const Icon(Icons.remove_circle_outline),
                ),
                Text('$_qty'),
                IconButton(
                  onPressed: () => setState(() => _qty++),
                  icon: const Icon(Icons.add_circle_outline),
                ),
              ],
            ),
            const SizedBox(height: 12),
            TextField(
              controller: _notes,
              minLines: 2,
              maxLines: 4,
              decoration: const InputDecoration(labelText: 'Notes', border: OutlineInputBorder()),
            ),
            const Spacer(),
            SizedBox(
              width: double.infinity,
              child: FilledButton(
                onPressed: () {
                  final PackingItem updated = widget.item.copyWith(
                    name: _name.text.trim(),
                    notes: _notes.text.trim().isEmpty ? null : _notes.text.trim(),
                    quantity: _qty,
                  );
                  Navigator.of(context).pop(updated);
                },
                child: const Text('Save'),
              ),
            )
          ],
        ),
      ),
    );
  }
}


