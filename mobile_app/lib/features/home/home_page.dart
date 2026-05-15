import 'dart:math' as math;
import 'dart:ui';

import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:flutter_animate/flutter_animate.dart';
import '../../routes/app_routes.dart';
import '../auth/auth_session.dart';
import '../auth/models.dart';

class HomePage extends StatefulWidget {
  const HomePage({super.key});

  @override
  State<HomePage> createState() => _HomePageState();
}

class _HomePageState extends State<HomePage> with SingleTickerProviderStateMixin {
  AuthUser? _user;
  int _refreshEpoch = 0;

  late final AnimationController _idleController;

  @override
  void initState() {
    super.initState();
    _idleController = AnimationController(
      vsync: this,
      duration: const Duration(milliseconds: 3000),
    )..repeat(reverse: true);

    _loadUser();
  }

  @override
  void dispose() {
    _idleController.dispose();
    super.dispose();
  }

  Future<void> _loadUser() async {
    final AuthUser? user = await AuthSession.load();
    if (!mounted) return;
    setState(() => _user = user);
  }

  Future<void> _onPullRefresh() async {
    await _loadUser();
    if (!mounted) return;
    setState(() => _refreshEpoch++);
    await Future<void>.delayed(const Duration(milliseconds: 280));
  }

  /// Time-of-day + slight per-tile variation for “state” icons.
  Color _themedIconColor(ColorScheme scheme, int hour, int tileIndex) {
    final double dayBlend = switch (hour) {
      < 5 => 0.38,
      >= 21 => 0.38,
      < 12 => 0.1,
      < 17 => 0.2,
      _ => 0.28,
    };
    final Color base =
        Color.lerp(scheme.primary, scheme.secondary, dayBlend)!;
    final double nudge = (tileIndex % 3) * 0.04;
    return Color.lerp(base, scheme.tertiary, nudge) ?? base;
  }

  String _greeting() {
    final int hour = DateTime.now().hour;
    if (hour < 5) return 'Good night';
    if (hour < 12) return 'Good morning';
    if (hour < 17) return 'Good afternoon';
    if (hour < 21) return 'Good evening';
    return 'Good night';
  }

  String _firstName() {
    final String? raw = _user?.name;
    if (raw == null || raw.trim().isEmpty) return 'Traveller';
    return raw.trim().split(RegExp(r'\s+')).first;
  }

  @override
  Widget build(BuildContext context) {
    final ThemeData theme = Theme.of(context);
    final TextTheme text = theme.textTheme;
    final ColorScheme colors = theme.colorScheme;
    final int hour = DateTime.now().hour;

    final List<_HomeAction> actions = <_HomeAction>[
      const _HomeAction(
        title: 'Mood Itinerary',
        subtitle: 'Plan by feeling',
        icon: Icons.auto_awesome_rounded,
        hoverIcon: Icons.explore_rounded,
        route: AppRoutes.itinerary,
      ),
      const _HomeAction(
        title: 'Packing Checklist',
        subtitle: 'Smart, tailored lists',
        icon: Icons.checklist_rounded,
        hoverIcon: Icons.luggage_rounded,
        route: AppRoutes.packing,
      ),
      const _HomeAction(
        title: 'Hazard Map',
        subtitle: 'Live alerts near you',
        icon: Icons.warning_amber_rounded,
        hoverIcon: Icons.shield_rounded,
        route: AppRoutes.hazardMap,
      ),
      const _HomeAction(
        title: 'Risk Around Me',
        subtitle: 'Scan my surroundings',
        icon: Icons.radar_rounded,
        hoverIcon: Icons.near_me_rounded,
        route: AppRoutes.riskAround,
      ),
      const _HomeAction(
        title: 'Emergency Mode',
        subtitle: 'Offline-first SOS',
        icon: Icons.sos_rounded,
        hoverIcon: Icons.medical_services_rounded,
        route: AppRoutes.emergency,
      ),
      const _HomeAction(
        title: 'AI Chat',
        subtitle: 'Ask Raahi anything',
        icon: Icons.smart_toy_rounded,
        hoverIcon: Icons.chat_bubble_rounded,
        route: AppRoutes.aiChat,
      ),
    ];

    return Scaffold(
      backgroundColor: Colors.transparent,
      body: SafeArea(
        child: RefreshIndicator(
          color: colors.primary,
          edgeOffset: 10,
          onRefresh: _onPullRefresh,
          child: CustomScrollView(
            physics: const AlwaysScrollableScrollPhysics(
              parent: BouncingScrollPhysics(),
            ),
            slivers: <Widget>[
            SliverToBoxAdapter(
              child: Padding(
                padding: const EdgeInsets.fromLTRB(20, 16, 20, 8),
                child: Row(
                  children: <Widget>[
                    const _BrandMark(),
                    const SizedBox(width: 12),
                    Expanded(
                      child: Column(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: <Widget>[
                          Text(
                            'Raahi AI',
                            style: text.titleMedium?.copyWith(
                              letterSpacing: 1.2,
                              color: colors.onSurface,
                              fontWeight: FontWeight.w800,
                            ),
                          ),
                          const SizedBox(height: 2),
                          Text(
                            'Unpredictable Roads, Predictable Plans',
                            style: text.labelSmall?.copyWith(
                              color: colors.onSurface.withValues(alpha: 0.7),
                              letterSpacing: 0.2,
                            ),
                          ),
                        ],
                      ),
                    ),
                    if (_user?.isAdmin == true)
                      _CircleIconButton(
                        icon: Icons.admin_panel_settings_outlined,
                        tooltip: 'Manage Users',
                        onTap: () => Navigator.of(context)
                            .pushNamed(AppRoutes.adminUsers),
                      ),
                    if (_user?.isAdmin == true) const SizedBox(width: 8),
                    _CircleIconButton(
                      icon: Icons.settings_outlined,
                      tooltip: 'Settings',
                      onTap: () => Navigator.of(context)
                          .pushNamed(AppRoutes.appSettings),
                    ),
                  ],
                ),
              ),
            ),
            SliverToBoxAdapter(
              child: Padding(
                padding: const EdgeInsets.fromLTRB(20, 16, 20, 4),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: <Widget>[
                    Text(
                      '${_greeting()},',
                      style: text.bodyLarge?.copyWith(
                        color: colors.onSurface.withValues(alpha: 0.7),
                      ),
                    ),
                    const SizedBox(height: 4),
                    Text(
                      '${_firstName()}.',
                      style: text.displaySmall?.copyWith(
                        height: 1.05,
                        color: colors.onSurface,
                      ),
                    ),
                    const SizedBox(height: 6),
                    Text(
                      'Where will today take you?',
                      style: text.bodyMedium?.copyWith(
                        color: colors.onSurface.withValues(alpha: 0.65),
                      ),
                    ),
                  ],
                ),
              ),
            ),
            SliverToBoxAdapter(
              child: Padding(
                padding: const EdgeInsets.fromLTRB(20, 18, 20, 8),
                child: _FeaturedCard(
                  onTap: () => Navigator.of(context)
                      .pushNamed(AppRoutes.itinerary),
                ),
              ),
            ),
            SliverToBoxAdapter(
              child: Padding(
                padding: const EdgeInsets.fromLTRB(20, 14, 20, 8),
                child: Row(
                  mainAxisAlignment: MainAxisAlignment.spaceBetween,
                  children: <Widget>[
                    Text(
                      'Explore',
                      style: text.titleMedium?.copyWith(
                        fontWeight: FontWeight.w700,
                      ),
                    ),
                    Text(
                      'Curated for you',
                      style: text.bodySmall?.copyWith(
                        color: colors.onSurface.withValues(alpha: 0.6),
                      ),
                    ),
                  ],
                ),
              ),
            ),
            SliverPadding(
              padding: const EdgeInsets.fromLTRB(20, 6, 20, 32),
              sliver: SliverGrid(
                gridDelegate: const SliverGridDelegateWithFixedCrossAxisCount(
                  crossAxisCount: 2,
                  crossAxisSpacing: 12,
                  mainAxisSpacing: 12,
                  childAspectRatio: 0.95,
                ),
                delegate: SliverChildBuilderDelegate(
                  (BuildContext context, int index) {
                    return _ActionCard(
                      key: ValueKey<String>(
                        '${actions[index].route}_$_refreshEpoch',
                      ),
                      action: actions[index],
                      index: index,
                      idleController: _idleController,
                      themedIconColor:
                          _themedIconColor(colors, hour, index),
                    );
                  },
                  childCount: actions.length,
                ),
              ),
            ),
          ],
        ),
      ),
    ),
    );
  }
}

class _BrandMark extends StatelessWidget {
  const _BrandMark();

  @override
  Widget build(BuildContext context) {
    return SizedBox(
      width: 44,
      height: 44,
      child: ClipRRect(
        borderRadius: BorderRadius.circular(14),
        child: Image.asset(
          'assets/Raahi AI Logo.png',
          fit: BoxFit.cover,
        ),
      ),
    );
  }
}

class _CircleIconButton extends StatelessWidget {
  final IconData icon;
  final String tooltip;
  final VoidCallback onTap;
  const _CircleIconButton({
    required this.icon,
    required this.tooltip,
    required this.onTap,
  });

  @override
  Widget build(BuildContext context) {
    final ColorScheme colors = Theme.of(context).colorScheme;
    return Tooltip(
      message: tooltip,
      child: InkResponse(
        onTap: onTap,
        radius: 24,
        child: Container(
          width: 42,
          height: 42,
          decoration: BoxDecoration(
            color: colors.surfaceContainerHighest,
            shape: BoxShape.circle,
            border: Border.all(color: colors.outlineVariant),
          ),
          alignment: Alignment.center,
          child: Icon(icon, size: 20, color: colors.onSurface),
        ),
      ),
    );
  }
}

/// Hero "Craft your journey" card with real frosted-glass treatment.
///
/// Glassmorphism needs **content behind the blur** — without it,
/// `BackdropFilter` has nothing to diffuse and the result looks identical
/// to a flat gradient.  So we paint vivid teal + orange "blobs" inside
/// the card's clip, then put a [BackdropFilter] on top.  The blur smears
/// those blobs into a soft teal → orange wash; a translucent white veil
/// and a hairline white border give it the signature glass feel.
class _FeaturedCard extends StatelessWidget {
  final VoidCallback onTap;
  const _FeaturedCard({required this.onTap});

  @override
  Widget build(BuildContext context) {
    final ColorScheme colors = Theme.of(context).colorScheme;
    final TextTheme text = Theme.of(context).textTheme;
    const BorderRadius radius = BorderRadius.all(Radius.circular(24));

    return ClipRRect(
      borderRadius: radius,
      child: Stack(
        children: <Widget>[
          // ── Solid teal (primary) base ──────────────────────────────
          Positioned.fill(
            child: ColoredBox(color: colors.primary),
          ),

          // ── Frosted glass overlay (subtle veil + edge) ─────────────
          Positioned.fill(
            child: BackdropFilter(
              filter: ImageFilter.blur(sigmaX: 24, sigmaY: 24),
              child: DecoratedBox(
                decoration: BoxDecoration(
                  gradient: LinearGradient(
                    begin: Alignment.topLeft,
                    end: Alignment.bottomRight,
                    colors: <Color>[
                      Colors.white.withValues(alpha: 0.10),
                      Colors.white.withValues(alpha: 0.02),
                    ],
                  ),
                  border: Border.all(
                    color: Colors.white.withValues(alpha: 0.32),
                    width: 1.2,
                  ),
                ),
              ),
            ),
          ),

          // Subtle inner highlight along the top edge — typical glass cue.
          Positioned(
            top: 0,
            left: 0,
            right: 0,
            child: Container(
              height: 1,
              decoration: BoxDecoration(
                gradient: LinearGradient(
                  colors: <Color>[
                    Colors.white.withValues(alpha: 0.0),
                    Colors.white.withValues(alpha: 0.55),
                    Colors.white.withValues(alpha: 0.0),
                  ],
                ),
              ),
            ),
          ),

          // ── Tap target + foreground content ────────────────────────
          Material(
            color: Colors.transparent,
            child: InkWell(
              onTap: onTap,
              borderRadius: radius,
              splashColor: Colors.white.withValues(alpha: 0.14),
              highlightColor: Colors.white.withValues(alpha: 0.05),
              child: Padding(
                padding: const EdgeInsets.all(20),
                child: Row(
                  children: <Widget>[
                    Expanded(
                      child: Column(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: <Widget>[
                          Text(
                            'CRAFT YOUR JOURNEY',
                            style: text.labelSmall?.copyWith(
                              letterSpacing: 2.2,
                              color: Colors.white.withValues(alpha: 0.9),
                              fontWeight: FontWeight.w700,
                            ),
                          ),
                          const SizedBox(height: 10),
                          Text(
                            'A trip tuned to your mood.',
                            style: text.titleLarge?.copyWith(
                              color: Colors.white,
                              height: 1.15,
                              shadows: <Shadow>[
                                Shadow(
                                  color: Colors.black.withValues(alpha: 0.18),
                                  blurRadius: 6,
                                ),
                              ],
                            ),
                          ),
                          const SizedBox(height: 6),
                          Text(
                            'Let AI design a route, day by day.',
                            style: text.bodyMedium?.copyWith(
                              color: Colors.white.withValues(alpha: 0.92),
                            ),
                          ),
                          const SizedBox(height: 14),
                          // Glass "Plan a trip" pill — same frost recipe.
                          ClipRRect(
                            borderRadius: BorderRadius.circular(999),
                            child: BackdropFilter(
                              filter: ImageFilter.blur(
                                sigmaX: 14,
                                sigmaY: 14,
                              ),
                              child: Container(
                                padding: const EdgeInsets.symmetric(
                                  horizontal: 14,
                                  vertical: 9,
                                ),
                                decoration: BoxDecoration(
                                  color: Colors.white.withValues(alpha: 0.92),
                                  borderRadius: BorderRadius.circular(999),
                                  border: Border.all(
                                    color: Colors.white
                                        .withValues(alpha: 0.6),
                                    width: 0.8,
                                  ),
                                ),
                                child: Row(
                                  mainAxisSize: MainAxisSize.min,
                                  children: <Widget>[
                                    Text(
                                      'Plan a trip',
                                      style: text.labelLarge?.copyWith(
                                        color: colors.primary,
                                        fontWeight: FontWeight.w700,
                                      ),
                                    ),
                                    const SizedBox(width: 6),
                                    Icon(
                                      Icons.arrow_forward_rounded,
                                      size: 16,
                                      color: colors.primary,
                                    ),
                                  ],
                                ),
                              ),
                            ),
                          ),
                        ],
                      ),
                    ),
                    const SizedBox(width: 8),
                    // Glass sparkle circle.
                    ClipOval(
                      child: BackdropFilter(
                        filter: ImageFilter.blur(sigmaX: 14, sigmaY: 14),
                        child: Container(
                          width: 64,
                          height: 64,
                          decoration: BoxDecoration(
                            shape: BoxShape.circle,
                            color: Colors.white.withValues(alpha: 0.18),
                            border: Border.all(
                              color: Colors.white.withValues(alpha: 0.45),
                              width: 1,
                            ),
                          ),
                          alignment: Alignment.center,
                          child: const Icon(
                            Icons.auto_awesome,
                            color: Colors.white,
                            size: 28,
                          ),
                        ),
                      ),
                    ),
                  ],
                ),
              ),
            ),
          ),
        ],
      ),
    );
  }
}


class _HomeAction {
  final String title;
  final String subtitle;
  final IconData icon;
  /// Shown when the pointer hovers the icon chip (desktop / mouse).
  final IconData hoverIcon;
  final String route;

  const _HomeAction({
    required this.title,
    required this.subtitle,
    required this.icon,
    required this.hoverIcon,
    required this.route,
  });
}

class _ActionCard extends StatefulWidget {
  final _HomeAction action;
  final int index;
  final AnimationController idleController;
  final Color themedIconColor;

  const _ActionCard({
    super.key,
    required this.action,
    required this.index,
    required this.idleController,
    required this.themedIconColor,
  });

  @override
  State<_ActionCard> createState() => _ActionCardState();
}

class _ActionCardState extends State<_ActionCard>
    with SingleTickerProviderStateMixin {
  late AnimationController _pressController;
  late Animation<double> _pressScale;
  bool _pressed = false;

  @override
  void initState() {
    super.initState();
    _pressController = AnimationController(
      vsync: this,
      duration: const Duration(milliseconds: 95),
    );
    _pressScale = Tween<double>(begin: 1.0, end: 0.96).animate(
      CurvedAnimation(parent: _pressController, curve: Curves.easeOutCubic),
    );
  }

  @override
  void dispose() {
    _pressController.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final ThemeData theme = Theme.of(context);
    final ColorScheme colors = theme.colorScheme;
    final TextTheme text = theme.textTheme;
    final _HomeAction action = widget.action;

    final bool isDark = theme.brightness == Brightness.dark;
    final BorderRadius tileRadius = BorderRadius.circular(20);

    // Frosted glass — keep veil light so [TravelAmbientBackground] motion reads through.
    final List<Color> glassFill = <Color>[
      Colors.white.withValues(alpha: isDark ? 0.055 : 0.16),
      Colors.white.withValues(alpha: isDark ? 0.02 : 0.06),
    ];
    final Color glassHighlight = Colors.white.withValues(alpha: isDark ? 0.07 : 0.22);
    final Color tileOutline = colors.primary.withValues(alpha: isDark ? 0.58 : 0.72);

    final Widget iconChip = SizedBox(
      width: 54,
      height: 54,
      child: Center(
        child: Icon(
          _pressed ? action.hoverIcon : action.icon,
          color: widget.themedIconColor,
          size: 30,
        ),
      ),
    );

    final Widget tile = DecoratedBox(
      decoration: BoxDecoration(
        borderRadius: tileRadius,
        boxShadow: <BoxShadow>[
          BoxShadow(
            color: colors.shadow.withValues(alpha: isDark ? 0.35 : 0.12),
            blurRadius: 22,
            offset: const Offset(0, 10),
            spreadRadius: -6,
          ),
        ],
      ),
      child: RepaintBoundary(
        child: ClipRRect(
          borderRadius: tileRadius,
          clipBehavior: Clip.antiAlias,
          child: Stack(
            fit: StackFit.expand,
            children: <Widget>[
              BackdropFilter(
                filter: ImageFilter.blur(sigmaX: 9, sigmaY: 9),
                child: DecoratedBox(
                  decoration: BoxDecoration(
                    gradient: LinearGradient(
                      begin: Alignment.topLeft,
                      end: Alignment.bottomRight,
                      colors: glassFill,
                    ),
                  ),
                ),
              ),
              Positioned(
                top: 0,
                left: 0,
                right: 0,
                child: IgnorePointer(
                  child: Container(
                    height: 1,
                    decoration: BoxDecoration(
                      gradient: LinearGradient(
                        colors: <Color>[
                          glassHighlight.withValues(alpha: 0),
                          glassHighlight,
                          glassHighlight.withValues(alpha: 0),
                        ],
                      ),
                    ),
                  ),
                ),
              ),
              Material(
                color: Colors.transparent,
                child: InkWell(
                  borderRadius: tileRadius,
                  splashColor: colors.primary.withValues(alpha: 0.12),
                  highlightColor: colors.onSurface.withValues(alpha: 0.05),
                  onTapDown: (_) {
                    HapticFeedback.lightImpact();
                    setState(() => _pressed = true);
                    _pressController.forward();
                  },
                  onTapUp: (_) {
                    setState(() => _pressed = false);
                    _pressController.reverse();
                    HapticFeedback.selectionClick();
                  },
                  onTapCancel: () {
                    setState(() => _pressed = false);
                    _pressController.reverse();
                  },
                  onTap: () => Navigator.of(context).pushNamed(action.route),
                  child: Padding(
                    padding: const EdgeInsets.all(16),
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: <Widget>[
                        DecoratedBox(
                          decoration: BoxDecoration(
                            gradient: LinearGradient(
                              begin: Alignment.topLeft,
                              end: Alignment.bottomRight,
                              colors: <Color>[
                                widget.themedIconColor.withValues(
                                  alpha: _pressed ? 0.16 : 0.10,
                                ),
                                widget.themedIconColor.withValues(
                                  alpha: _pressed ? 0.08 : 0.045,
                                ),
                              ],
                            ),
                            borderRadius: BorderRadius.circular(16),
                            border: Border.all(
                              color: Colors.white.withValues(
                                alpha: isDark ? 0.16 : 0.36,
                              ),
                              width: 1,
                            ),
                          ),
                          child: iconChip,
                        ),
                        const Spacer(),
                        Text(
                          action.title,
                          style: text.titleMedium?.copyWith(
                            fontWeight: FontWeight.w700,
                            height: 1.15,
                            shadows: <Shadow>[
                              Shadow(
                                color: colors.shadow.withValues(alpha: 0.12),
                                blurRadius: 4,
                                offset: const Offset(0, 1),
                              ),
                            ],
                          ),
                        ),
                        const SizedBox(height: 2),
                        Text(
                          action.subtitle,
                          maxLines: 1,
                          overflow: TextOverflow.ellipsis,
                          style: text.bodySmall?.copyWith(
                            color: colors.onSurface.withValues(alpha: 0.78),
                            fontWeight: FontWeight.w500,
                          ),
                        ),
                      ],
                    ),
                  ),
                ),
              ),
              // Primary (teal) stroke inside the clip so it tracks transforms and
              // avoids subpixel shimmer vs an outer [DecoratedBox] border.
              Positioned.fill(
                child: IgnorePointer(
                  child: DecoratedBox(
                    decoration: BoxDecoration(
                      borderRadius: tileRadius,
                      border: Border.all(color: tileOutline, width: 1),
                    ),
                  ),
                ),
              ),
            ],
          ),
        ),
      ),
    );

    final Widget animatedTile = tile
        .animate(delay: (42 * widget.index).ms)
        .fadeIn(
          duration: 400.ms,
          curve: Curves.easeOutCubic,
        )
        .slideY(
          begin: 0.06,
          end: 0,
          duration: 400.ms,
          curve: Curves.easeOutCubic,
        )
        .scale(
          begin: const Offset(0.94, 0.94),
          end: const Offset(1, 1),
          duration: 400.ms,
          curve: Curves.easeOutCubic,
        );

    return AnimatedBuilder(
      animation: Listenable.merge(<Listenable>[
        widget.idleController,
        _pressController,
      ]),
      builder: (BuildContext context, Widget? child) {
        final double phase =
            widget.idleController.value * math.pi * 2 + widget.index * 0.55;
        final double idleScale =
            1.0 + 0.0075 * math.sin(phase);
        final double combined = idleScale * _pressScale.value;
        return Transform.scale(
          scale: combined,
          child: child,
        );
      },
      child: animatedTile,
    );
  }
}