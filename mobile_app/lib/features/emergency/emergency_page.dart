import 'package:flutter/material.dart';
import '../../routes/app_routes.dart';
import '../../widgets/app_footer_nav.dart';

class EmergencyPage extends StatelessWidget {
  const EmergencyPage({super.key});

  @override
  Widget build(BuildContext context) {
    final List<_CardLink> cards = <_CardLink>[
      _CardLink('Offline Downloads', Icons.download_rounded, AppRoutes.emergencyDownloads),
      _CardLink('Safe Points', Icons.place_rounded, AppRoutes.emergencySafePoints),
      _CardLink('SOS Setup & Contacts', Icons.contact_phone_rounded, AppRoutes.emergencySosSetup),
      _CardLink('Queued Messages', Icons.schedule_send_rounded, AppRoutes.emergencyOutbox),
      _CardLink('Settings', Icons.settings_rounded, AppRoutes.emergencySettings),
    ];
    return Scaffold(
      appBar: AppBar(title: const Text('Emergency Mode')),
      body: Padding(
        padding: const EdgeInsets.all(16.0),
        child: GridView.builder(
          gridDelegate: const SliverGridDelegateWithFixedCrossAxisCount(
            crossAxisCount: 2,
            crossAxisSpacing: 12,
            mainAxisSpacing: 12,
            childAspectRatio: 1.1,
          ),
          itemCount: cards.length,
          itemBuilder: (BuildContext context, int i) {
            final _CardLink c = cards[i];
            return InkWell(
              borderRadius: BorderRadius.circular(16),
              onTap: () => Navigator.of(context).pushNamed(c.route),
              child: Ink(
                decoration: BoxDecoration(
                  color: Theme.of(context).colorScheme.surface,
                  borderRadius: BorderRadius.circular(16),
                  border: Border.all(color: Theme.of(context).colorScheme.outlineVariant),
                ),
                child: Column(
                  mainAxisAlignment: MainAxisAlignment.center,
                  children: <Widget>[
                    Icon(c.icon, size: 36, color: Theme.of(context).colorScheme.primary),
                    const SizedBox(height: 12),
                    Text(c.title, textAlign: TextAlign.center),
                  ],
                ),
              ),
            );
          },
        ),
      ),
    );
  }
}

class _CardLink {
  final String title;
  final IconData icon;
  final String route;
  const _CardLink(this.title, this.icon, this.route);
}


