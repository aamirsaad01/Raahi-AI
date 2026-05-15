import 'dart:math' as math;

import 'package:flutter/material.dart';

/// Drifting travel / tourism + AI icons behind page content.
///
/// Intended to sit above a solid [ColorScheme.surface] layer and below the
/// navigator. Uses [IgnorePointer] so gestures pass through. Overall strength
/// is controlled by [opacity] (default 0.1 = 10%).
class TravelAmbientBackground extends StatefulWidget {
  const TravelAmbientBackground({
    super.key,
    this.opacity = 0.1,
  });

  static const int gridCols = 9;
  static const int gridRows = 7;

  /// Effective strength of the decorative layer (multiplies icon alpha).
  final double opacity;

  @override
  State<TravelAmbientBackground> createState() =>
      _TravelAmbientBackgroundState();
}

class _TravelAmbientBackgroundState extends State<TravelAmbientBackground>
    with SingleTickerProviderStateMixin {
  late AnimationController _controller;

  /// Travel + tourism + AI — cycled across a dense grid.
  static const List<IconData> _icons = <IconData>[
    Icons.flight_takeoff_rounded,
    Icons.flight_land_rounded,
    Icons.luggage_rounded,
    Icons.train_rounded,
    Icons.directions_boat_rounded,
    Icons.directions_car_rounded,
    Icons.hotel_rounded,
    Icons.restaurant_rounded,
    Icons.local_cafe_rounded,
    Icons.beach_access_rounded,
    Icons.terrain_rounded,
    Icons.map_rounded,
    Icons.explore_rounded,
    Icons.photo_camera_rounded,
    Icons.hiking_rounded,
    Icons.museum_rounded,
    Icons.airport_shuttle_rounded,
    Icons.public_rounded,
    Icons.wb_sunny_rounded,
    Icons.nightlight_round,
    Icons.attractions_rounded,
    Icons.sailing_rounded,
    Icons.smart_toy_rounded,
    Icons.auto_awesome_rounded,
    Icons.psychology_rounded,
    Icons.auto_graph_rounded,
    Icons.analytics_rounded,
    Icons.bolt_rounded,
    Icons.tips_and_updates_rounded,
    Icons.memory_rounded,
    Icons.account_tree_rounded,
    Icons.data_object_rounded,
    Icons.model_training_rounded,
    Icons.draw_rounded,
    Icons.forum_rounded,
    Icons.support_agent_rounded,
    Icons.language_rounded,
    Icons.travel_explore_rounded,
    Icons.festival_rounded,
    Icons.park_rounded,
    Icons.diversity_3_rounded,
    Icons.restaurant_menu_rounded,
    Icons.emoji_transportation_rounded,
  ];

  static const int _cellCount =
      TravelAmbientBackground.gridCols * TravelAmbientBackground.gridRows;

  @override
  void initState() {
    super.initState();
    _controller = AnimationController(
      vsync: this,
      duration: const Duration(seconds: 25),
    )..repeat();
  }

  @override
  void dispose() {
    _controller.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final ColorScheme scheme = Theme.of(context).colorScheme;
    // Saturated blend so icons stay visible after layer [Opacity] applies.
    final Color iconColor = Color.alphaBlend(
      scheme.primary.withValues(alpha: 0.92),
      scheme.onSurface.withValues(alpha: 0.55),
    );

    return RepaintBoundary(
      child: IgnorePointer(
        child: LayoutBuilder(
          builder: (BuildContext context, BoxConstraints constraints) {
            if (!constraints.hasBoundedWidth || !constraints.hasBoundedHeight) {
              return const SizedBox.shrink();
            }
            final double w = constraints.maxWidth;
            final double h = constraints.maxHeight;
            if (w < 8 || h < 8) {
              return const SizedBox.shrink();
            }

            return Opacity(
              opacity: widget.opacity.clamp(0.0, 1.0),
              child: AnimatedBuilder(
                animation: _controller,
                builder: (BuildContext context, Widget? _) {
                  final double t = _controller.value * math.pi * 2;
                  return Stack(
                    clipBehavior: Clip.none,
                    children: <Widget>[
                      for (int i = 0; i < _cellCount; i++)
                        _DriftIcon(
                          icon: _icons[i % _icons.length],
                          color: iconColor,
                          index: i,
                          width: w,
                          height: h,
                          t: t,
                        ),
                    ],
                  );
                },
              ),
            );
          },
        ),
      ),
    );
  }
}

class _DriftIcon extends StatelessWidget {
  const _DriftIcon({
    required this.icon,
    required this.color,
    required this.index,
    required this.width,
    required this.height,
    required this.t,
  });

  final IconData icon;
  final Color color;
  final int index;
  final double width;
  final double height;
  final double t;

  static const int _cols = TravelAmbientBackground.gridCols;
  static const int _rows = TravelAmbientBackground.gridRows;

  @override
  Widget build(BuildContext context) {
    final double phase = index * 0.61;
    final double slow = t * 2.65;
    final double dx = math.sin(slow + phase) * width * 0.048 +
        math.cos(slow * 0.72 + phase * 1.3) * width * 0.026;
    final double dy = math.cos(slow * 0.52 + phase * 1.08) * height * 0.055 +
        math.sin(slow * 0.62 + phase) * height * 0.03;

    final double cellW = width / _cols;
    final double cellH = height / _rows;
    final int ci = index % _cols;
    final int ri = index ~/ _cols;
    final double bx = (ci + 0.5) * cellW;
    final double by = (ri + 0.5) * cellH;
    final double jitterX = math.sin(index * 2.17 + 0.3) * cellW * 0.12;
    final double jitterY = math.cos(index * 1.91 + 0.5) * cellH * 0.12;

    final double size = 17 + (index % 4) * 4.0;
    final double angle = math.sin(t * 0.42 + phase) * 0.07;

    final double half = size * 0.5;
    final double left = (bx + jitterX + dx - half)
        .clamp(half, math.max(half, width - half));
    final double top = (by + jitterY + dy - half)
        .clamp(half, math.max(half, height - half));
    return Positioned(
      left: left,
      top: top,
      child: Transform.rotate(
        angle: angle,
        child: Icon(icon, size: size, color: color),
      ),
    );
  }
}
