import 'package:flutter/material.dart';
import '../../routes/app_routes.dart';
import '../../widgets/app_footer_nav.dart';

class HomePage extends StatelessWidget {
  const HomePage({super.key});

  @override
  Widget build(BuildContext context) {
    final ThemeData theme = Theme.of(context);
    final TextTheme textTheme = theme.textTheme;

    final List<_HomeAction> actions = <_HomeAction>[
      _HomeAction(
        title: 'Mood Itinerary',
        icon: Icons.auto_awesome,
        route: AppRoutes.itinerary,
      ),
      _HomeAction(
        title: 'Packing Checklist',
        icon: Icons.checklist_rounded,
        route: AppRoutes.packing,
      ),
      _HomeAction(
        title: 'Hazard Map',
        icon: Icons.warning_amber_rounded,
        route: AppRoutes.hazardMap,
      ),
      _HomeAction(
        title: 'Emergency Mode',
        icon: Icons.sos_rounded,
        route: AppRoutes.emergency,
      ),
      _HomeAction(
        title: 'Group Chat',
        icon: Icons.forum_rounded,
        route: AppRoutes.groupChat,
      ),
      _HomeAction(
        title: 'AI Chat (Urdu)',
        icon: Icons.smart_toy_rounded,
        route: AppRoutes.aiChat,
      ),
    ];

    final ColorScheme colors = theme.colorScheme;
    return Scaffold(
      appBar: AppBar(
        backgroundColor: colors.primary,
        foregroundColor: Colors.white,
        title: const Text('Raahi AI'),
      ),
      body: Padding(
        padding: const EdgeInsets.all(16.0),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: <Widget>[
            Text('Your Travel Companion', style: textTheme.titleLarge),
            const SizedBox(height: 12),
            Expanded(
              child: GridView.builder(
                gridDelegate: const SliverGridDelegateWithFixedCrossAxisCount(
                  crossAxisCount: 2,
                  crossAxisSpacing: 12,
                  mainAxisSpacing: 12,
                  childAspectRatio: 1.1,
                ),
                itemCount: actions.length,
                itemBuilder: (BuildContext context, int index) {
                  final _HomeAction action = actions[index];
                  return _ActionCard(action: action);
                },
              ),
            ),
          ],
        ),
      ),
    );
  }
}

class _HomeAction {
  final String title;
  final IconData icon;
  final String route;

  const _HomeAction({
    required this.title,
    required this.icon,
    required this.route,
  });
}

class _ActionCard extends StatelessWidget {
  final _HomeAction action;

  const _ActionCard({required this.action});

  @override
  Widget build(BuildContext context) {
    final ColorScheme colors = Theme.of(context).colorScheme;
    return InkWell(
      borderRadius: BorderRadius.circular(16),
      onTap: () => Navigator.of(context).pushNamed(action.route),
      child: Ink(
        decoration: BoxDecoration(
          color: colors.surface,
          borderRadius: BorderRadius.circular(16),
          border: Border.all(color: colors.outlineVariant),
        ),
        child: Padding(
          padding: const EdgeInsets.all(16.0),
          child: Column(
            mainAxisAlignment: MainAxisAlignment.center,
            children: <Widget>[
              Icon(action.icon, size: 36, color: colors.primary),
              const SizedBox(height: 12),
              Text(action.title, textAlign: TextAlign.center),
            ],
          ),
        ),
      ),
    );
  }
}



