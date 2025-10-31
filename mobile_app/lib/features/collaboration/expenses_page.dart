import 'package:flutter/material.dart';
import '../../routes/app_routes.dart';
import 'models.dart';

class ExpensesPage extends StatelessWidget {
  const ExpensesPage({super.key});

  @override
  Widget build(BuildContext context) {
    final List<Expense> expenses = <Expense>[
      Expense(
        id: 'e1',
        description: 'Hotel booking',
        amount: 15000,
        currency: 'PKR',
        paidBy: 'Ahmed',
        splitBetween: const <String>['Ahmed', 'Sara'],
        timestamp: DateTime.now().subtract(const Duration(days: 1)),
      ),
    ];

    return Scaffold(
      appBar: AppBar(
        title: const Text('Expenses'),
        actions: <Widget>[
          Padding(
            padding: const EdgeInsets.only(right: 8.0),
            child: _IconFilledButton(
              icon: Icons.add_rounded,
              tooltip: 'Add Expense',
              onTap: () => Navigator.of(context).pushNamed(AppRoutes.collaborationExpenseAdd),
            ),
          ),
        ],
      ),
      body: Column(
        children: <Widget>[
          Expanded(
            child: ListView.separated(
              padding: const EdgeInsets.all(12),
              itemCount: expenses.length,
              separatorBuilder: (_, __) => const SizedBox(height: 8),
              itemBuilder: (BuildContext context, int i) {
                final Expense e = expenses[i];
                return Card(
                  child: ListTile(
                    title: Text(e.description),
                    subtitle: Text('Paid by ${e.paidBy} • ${e.splitBetween.length} people'),
                    trailing: Text('${e.amount} ${e.currency}'),
                  ),
                );
              },
            ),
          ),
          Container(
            padding: const EdgeInsets.all(16),
            decoration: BoxDecoration(color: Theme.of(context).colorScheme.surfaceVariant),
            child: Column(
              children: <Widget>[
                const Text('Balances', style: TextStyle(fontWeight: FontWeight.bold)),
                const SizedBox(height: 8),
                Text('Ahmed owes: PKR 7500'),
                Text('Sara owes: PKR 7500'),
              ],
            ),
          ),
        ],
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
    if (tooltip != null) return Tooltip(message: tooltip!, child: btn);
    return btn;
  }
}

