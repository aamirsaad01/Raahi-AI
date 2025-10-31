import 'package:flutter/material.dart';
import '../../routes/app_routes.dart';
import 'models.dart';

class PollsPage extends StatelessWidget {
  const PollsPage({super.key});

  @override
  Widget build(BuildContext context) {
    final List<Poll> polls = <Poll>[
      Poll(
        id: 'p1',
        question: 'Where should we have dinner?',
        options: <String>['Restaurant A', 'Restaurant B', 'Street Food'],
        votes: <String, String>{'u1': 'Restaurant A', 'u2': 'Street Food'},
      ),
    ];

    return Scaffold(
      appBar: AppBar(
        title: const Text('Polls'),
        actions: <Widget>[
          Padding(
            padding: const EdgeInsets.only(right: 8.0),
            child: _IconFilledButton(
              icon: Icons.add_rounded,
              tooltip: 'Create Poll',
              onTap: () => Navigator.of(context).pushNamed(AppRoutes.collaborationPollCreate),
            ),
          ),
        ],
      ),
      body: ListView.builder(
        padding: const EdgeInsets.all(12),
        itemCount: polls.length,
        itemBuilder: (BuildContext context, int i) {
          final Poll p = polls[i];
          return Card(
            child: Padding(
              padding: const EdgeInsets.all(12.0),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: <Widget>[
                  Text(p.question, style: Theme.of(context).textTheme.titleMedium),
                  const SizedBox(height: 8),
                  ...p.options.map((String opt) {
                    final int count = p.votes.values.where((String v) => v == opt).length;
                    return Padding(
                      padding: const EdgeInsets.symmetric(vertical: 4.0),
                      child: Row(
                        children: <Widget>[
                          Expanded(
                            child: LinearProgressIndicator(value: count / p.votes.length),
                          ),
                          const SizedBox(width: 8),
                          Text('$count'),
                        ],
                      ),
                    );
                  }),
                ],
              ),
            ),
          );
        },
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

