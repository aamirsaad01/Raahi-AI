import 'package:flutter/material.dart';
import 'models.dart';

class AddExpensePage extends StatefulWidget {
  const AddExpensePage({super.key});

  @override
  State<AddExpensePage> createState() => _AddExpensePageState();
}

class _AddExpensePageState extends State<AddExpensePage> {
  final TextEditingController _desc = TextEditingController();
  final TextEditingController _amount = TextEditingController();
  String _currency = 'PKR';
  String _paidBy = 'Ahmed';
  final Set<String> _splitBetween = <String>{'Ahmed', 'Sara'};

  @override
  void dispose() {
    _desc.dispose();
    _amount.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('Add Expense')),
      body: Padding(
        padding: const EdgeInsets.all(16.0),
        child: Column(
          children: <Widget>[
            TextField(
              controller: _desc,
              decoration: const InputDecoration(labelText: 'Description', border: OutlineInputBorder()),
            ),
            const SizedBox(height: 12),
            Row(
              children: <Widget>[
                Expanded(
                  child: TextField(
                    controller: _amount,
                    keyboardType: TextInputType.number,
                    decoration: const InputDecoration(labelText: 'Amount', border: OutlineInputBorder()),
                  ),
                ),
                const SizedBox(width: 12),
                DropdownButton<String>(
                  value: _currency,
                  items: const <DropdownMenuItem<String>>[
                    DropdownMenuItem<String>(value: 'PKR', child: Text('PKR')),
                    DropdownMenuItem<String>(value: 'USD', child: Text('USD')),
                  ],
                  onChanged: (String? v) => setState(() => _currency = v ?? 'PKR'),
                ),
              ],
            ),
            const SizedBox(height: 12),
            DropdownButtonFormField<String>(
              value: _paidBy,
              decoration: const InputDecoration(labelText: 'Paid By', border: OutlineInputBorder()),
              items: <String>['Ahmed', 'Sara'].map((String n) => DropdownMenuItem<String>(value: n, child: Text(n))).toList(),
              onChanged: (String? v) => setState(() => _paidBy = v ?? 'Ahmed'),
            ),
            const SizedBox(height: 12),
            Wrap(
              spacing: 8,
              children: <String>['Ahmed', 'Sara'].map((String n) => FilterChip(
                label: Text(n),
                selected: _splitBetween.contains(n),
                onSelected: (bool s) => setState(() => s ? _splitBetween.add(n) : _splitBetween.remove(n)),
              )).toList(),
            ),
            const Spacer(),
            SizedBox(
              width: double.infinity,
              child: FilledButton(
                onPressed: () {
                  ScaffoldMessenger.of(context).showSnackBar(const SnackBar(content: Text('Expense added (stub)')));
                  Navigator.of(context).pop();
                },
                child: const Text('Add'),
              ),
            )
          ],
        ),
      ),
    );
  }
}

