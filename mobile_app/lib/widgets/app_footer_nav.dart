import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import '../routes/app_routes.dart';

/// Tabs surfaced on the floating bottom nav.
enum FooterTab { home, itinerary, packing, hazards, emergency, ai }

/// Floating pill-shaped bottom navigation.
///
/// Sits above the page content with horizontal + bottom margins. Teal bar in
/// light mode with a white circle for the active tab; dark mode uses a dark
/// pill with primary circle for the active tab. Flat (no drop shadow) so it
/// does not cast a shadow onto the page above.
class AppFooterNav extends StatelessWidget {
  final FooterTab? current;
  final void Function(FooterTab tab)? onTap;

  const AppFooterNav({super.key, required this.current, this.onTap});

  @override
  Widget build(BuildContext context) {
    final ThemeData theme = Theme.of(context);
    final ColorScheme colors = theme.colorScheme;
    final bool isDark = theme.brightness == Brightness.dark;

    final List<_FooterItem> items = const <_FooterItem>[
      _FooterItem(
        tab: FooterTab.home,
        icon: Icons.home_rounded,
        label: 'Home',
        route: AppRoutes.home,
      ),
      _FooterItem(
        tab: FooterTab.itinerary,
        icon: Icons.auto_awesome_rounded,
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
        tab: FooterTab.ai,
        icon: Icons.smart_toy_rounded,
        label: 'AI Chat',
        route: AppRoutes.aiChat,
      ),
    ];

    // Teal pill, white pill in dark mode flips to a subtle dark surface so
    // the bar does not glow.
    final Color barColor = isDark ? colors.surfaceContainerHighest : colors.primary;
    final Color borderColor = isDark
        ? Colors.white.withValues(alpha: 0.06)
        : Colors.white.withValues(alpha: 0.18);

    final ShapeBorder pillShape = RoundedRectangleBorder(
      borderRadius: BorderRadius.circular(999),
      side: BorderSide(color: borderColor, width: 1),
    );

    return SafeArea(
      top: false,
      minimum: const EdgeInsets.only(bottom: 12),
      child: Padding(
        padding: const EdgeInsets.fromLTRB(14, 0, 14, 6),
        child: Material(
          color: barColor,
          // No drop shadow — kept as a flat pill so it does not visually
          // bleed onto the page above (e.g. on form screens).
          elevation: 0,
          shadowColor: Colors.transparent,
          surfaceTintColor: Colors.transparent,
          shape: pillShape,
          clipBehavior: Clip.antiAlias,
          child: SizedBox(
            height: 64,
            child: Padding(
              padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 8),
              child: Row(
                mainAxisAlignment: MainAxisAlignment.spaceEvenly,
                children: items
                    .map((_FooterItem item) => _FooterButton(
                          item: item,
                          isActive: current == item.tab,
                          onTap: onTap,
                        ))
                    .toList(),
              ),
            ),
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

  const _FooterItem({
    required this.tab,
    required this.icon,
    required this.label,
    required this.route,
  });
}

class _FooterButton extends StatelessWidget {
  final _FooterItem item;
  final bool isActive;
  final void Function(FooterTab tab)? onTap;

  const _FooterButton({
    required this.item,
    required this.isActive,
    this.onTap,
  });

  void _handleTap(BuildContext context) {
    HapticFeedback.selectionClick();
    if (isActive) return;
    if (onTap != null) {
      onTap!(item.tab);
      return;
    }
    if (item.tab == FooterTab.home) {
      Navigator.of(context).pushNamedAndRemoveUntil(
        item.route,
        (Route<dynamic> r) => false,
      );
    } else {
      Navigator.of(context).pushNamed(item.route);
    }
  }

  @override
  Widget build(BuildContext context) {
    final ColorScheme colors = Theme.of(context).colorScheme;
    final bool isDark = Theme.of(context).brightness == Brightness.dark;

    // Light: teal pill → white circle for active, teal icon inside.
    // Dark : dark pill → primary circle for active, white icon inside.
    final Color activeBg = isDark ? colors.primary : colors.onPrimary;
    final Color activeFg = isDark ? colors.onPrimary : colors.primary;
    final Color inactiveFg = isDark
        ? colors.onSurface.withValues(alpha: 0.62)
        : colors.onPrimary.withValues(alpha: 0.78);

    return Semantics(
      label: item.label,
      button: true,
      selected: isActive,
      child: InkResponse(
        onTap: () => _handleTap(context),
        radius: 28,
        highlightShape: BoxShape.circle,
        child: AnimatedContainer(
          duration: const Duration(milliseconds: 220),
          curve: Curves.easeOutCubic,
          width: 44,
          height: 44,
          decoration: BoxDecoration(
            color: isActive ? activeBg : Colors.transparent,
            shape: BoxShape.circle,
          ),
          alignment: Alignment.center,
          child: AnimatedSwitcher(
            duration: const Duration(milliseconds: 220),
            child: Icon(
              item.icon,
              key: ValueKey<bool>(isActive),
              size: 22,
              color: isActive ? activeFg : inactiveFg,
            ),
          ),
        ),
      ),
    );
  }
}
