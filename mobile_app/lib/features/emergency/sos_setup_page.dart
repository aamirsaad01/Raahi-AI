import 'package:flutter/material.dart';

class SosSetupPage extends StatefulWidget {
  const SosSetupPage({super.key});

  @override
  State<SosSetupPage> createState() => _SosSetupPageState();
}

class _SosSetupPageState extends State<SosSetupPage> {
  final TextEditingController _template = TextEditingController(text: 'SOS! I need help. My last location is:');
  final List<String> contacts = <String>['+92 300 1234567'];

  @override
  void dispose() {
    _template.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('SOS Setup & Contacts')),
      body: Padding(
        padding: const EdgeInsets.all(16.0),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: <Widget>[
            TextField(
              controller: _template,
              minLines: 2,
              maxLines: 4,
              decoration: const InputDecoration(labelText: 'Message Template', border: OutlineInputBorder()),
            ),
            const SizedBox(height: 16),
            Text('Trusted Contacts', style: Theme.of(context).textTheme.titleMedium),
            const SizedBox(height: 8),
            ...contacts.map((String c) => ListTile(
                  leading: const Icon(Icons.contact_phone_rounded),
                  title: Text(c),
                  trailing: IconButton(onPressed: () {}, icon: const Icon(Icons.delete_outline)),
                )),
            const Spacer(),
            SizedBox(
              width: double.infinity,
              child: FilledButton.icon(
                onPressed: () {},
                icon: const Icon(Icons.add_rounded),
                label: const Text('Add Contact'),
              ),
            )
          ],
        ),
      ),
    );
  }
}


