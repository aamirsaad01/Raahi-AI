import 'package:flutter/material.dart';
import 'models.dart';

class CreatePollPage extends StatefulWidget {
  const CreatePollPage({super.key});

  @override
  State<CreatePollPage> createState() => _CreatePollPageState();
}

class _CreatePollPageState extends State<CreatePollPage> {
  final TextEditingController _question = TextEditingController();
  final List<TextEditingController> _options = <TextEditingController>[
    TextEditingController(),
    TextEditingController(),
  ];

  @override
  void dispose() {
    _question.dispose();
    for (final TextEditingController c in _options) c.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('Create Poll')),
      body: Padding(
        padding: const EdgeInsets.all(16.0),
        child: Column(
          children: <Widget>[
            TextField(
              controller: _question,
              decoration: const InputDecoration(labelText: 'Question', border: OutlineInputBorder()),
            ),
            const SizedBox(height: 12),
            ..._options.asMap().entries.map((MapEntry<int, TextEditingController> e) {
              return Padding(
                padding: const EdgeInsets.only(bottom: 8.0),
                child: Row(
                  children: <Widget>[
                    Expanded(
                      child: TextField(
                        controller: e.value,
                        decoration: InputDecoration(
                          labelText: 'Option ${e.key + 1}',
                          border: const OutlineInputBorder(),
                        ),
                      ),
                    ),
                    if (_options.length > 2)
                      IconButton(
                        onPressed: () => setState(() => _options.removeAt(e.key)),
                        icon: const Icon(Icons.remove_circle_outline),
                      ),
                  ],
                ),
              );
            }),
            TextButton.icon(
              onPressed: () => setState(() => _options.add(TextEditingController())),
              icon: const Icon(Icons.add_rounded),
              label: const Text('Add Option'),
            ),
            const Spacer(),
            SizedBox(
              width: double.infinity,
              child: FilledButton(
                onPressed: () {
                  ScaffoldMessenger.of(context).showSnackBar(const SnackBar(content: Text('Poll created (stub)')));
                  Navigator.of(context).pop();
                },
                child: const Text('Create'),
              ),
            )
          ],
        ),
      ),
    );
  }
}

