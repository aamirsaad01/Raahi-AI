import 'package:flutter/material.dart';
import '../routes/app_routes.dart';

enum FooterTab { home, itinerary, packing, hazards, emergency, chat, ai }

class AppFooterNav extends StatelessWidget {
  final FooterTab? current;
  final void Function(FooterTab tab)? onTap;

  const AppFooterNav({super.key, required this.current, this.onTap});

  @override
  Widget build(BuildContext context) {
    final ColorScheme colors = Theme.of(context).colorScheme;
    final List<_FooterItem> items = <_FooterItem>[
      _FooterItem(
        tab: FooterTab.home,
        icon: Icons.home_rounded,
        label: 'Home',
        route: AppRoutes.home,
      ),
      _FooterItem(
        tab: FooterTab.itinerary,
        icon: Icons.auto_awesome,
        label: 'Itinerary',
        route: AppRoutes.itinerary,
      ),
      _FooterItem(
        tab: FooterTab.packing,
        icon: Icons.checklist_rounded,
        label: 'Packing',
        route: AppRoutes.packing,
      ),
      _FooterItem(
        tab: FooterTab.hazards,
        icon: Icons.warning_amber_rounded,
        label: 'Hazards',
        route: AppRoutes.hazardMap,
      ),
      _FooterItem(
        tab: FooterTab.emergency,
        icon: Icons.sos_rounded,
        label: 'Emergency',
        route: AppRoutes.emergency,
      ),
      _FooterItem(
        tab: FooterTab.chat,
        icon: Icons.groups_rounded,
        label: 'Collaboration',
        route: AppRoutes.collaboration,
      ),
      _FooterItem(
        tab: FooterTab.ai,
        icon: Icons.smart_toy_rounded,
        label: 'AI Chat',
        route: AppRoutes.aiChat,
      ),
    ];

    return Material(
      color: colors.primary,
      child: SafeArea(
        top: false,
        child: Padding(
          padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 6),
          child: Row(
            mainAxisAlignment: MainAxisAlignment.spaceBetween,
            children: items
                .map(( _FooterItem item ) => _FooterButton(
                      item: item,
                      isActive: current == item.tab,
                      onTap: onTap, // pass parent onTap!
                    ))
                .toList(),
          ),
        ),
      ),
    );
  }
}

class _FooterItem {
  final FooterTab tab;
  final IconData icon;
  final String label;
  final String route;

  const _FooterItem({required this.tab, required this.icon, required this.label, required this.route});
}

class _FooterButton extends StatelessWidget {
  final _FooterItem item;
  final bool isActive;
  final void Function(FooterTab tab)? onTap; // add this field

  const _FooterButton({required this.item, required this.isActive, this.onTap}); // update constructor

  @override
  Widget build(BuildContext context) {
    final ColorScheme colors = Theme.of(context).colorScheme;
    final Color bg = isActive ? Colors.white : Colors.transparent;
    final Color fg = isActive ? colors.primary : Colors.white;
    return Expanded(
      child: InkWell(
        borderRadius: BorderRadius.circular(24),
        onTap: () {
          if (isActive) return;
          if (onTap != null) {
            onTap!(item.tab);
            return;
          }
          if (item.tab == FooterTab.home) {
            Navigator.of(context).pushNamedAndRemoveUntil(item.route, (Route<dynamic> r) => false);
          } else {
            Navigator.of(context).pushNamed(item.route);
          }
        },
        child: AnimatedContainer(
          duration: const Duration(milliseconds: 200),
          padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 8),
          decoration: BoxDecoration(
            color: bg,
            borderRadius: BorderRadius.circular(24),
          ),
          child: Icon(item.icon, color: fg, size: 20),
        ),
      ),
    );
  }
}


