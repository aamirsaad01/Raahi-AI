import 'package:flutter/material.dart';

/// App-wide constants
class AppConstants {
  /// Matches [AppFooterNav]: `SafeArea` enforces at least 12px bottom inset
  /// before the pill; outer `Padding` bottom 6; pill `SizedBox` height 64.
  static const double _footerSafeMinBottom = 12;
  static const double _footerOuterBottomPad = 6;
  static const double _footerBarHeight = 64;
  /// Small air gap between pill top and FABs / pinned inputs (tight but readable).
  static const double _footerOverlayGapAbovePill = 3;
  static const double _footerScrollExtraBelowOverlay = 6;

  /// Bottom inset for FABs and pinned composer rows — just above the floating pill.
  static double footerOverlayBottomPadding(BuildContext context) {
    final double sys = MediaQuery.paddingOf(context).bottom;
    final double bottomSafe =
        sys > _footerSafeMinBottom ? sys : _footerSafeMinBottom;
    return bottomSafe +
        _footerOuterBottomPad +
        _footerBarHeight +
        _footerOverlayGapAbovePill;
  }

  /// Bottom padding for scroll views so the last items clear the pill.
  static double footerScrollBottomPadding(BuildContext context) =>
      footerOverlayBottomPadding(context) + _footerScrollExtraBelowOverlay;

  /// For `.add(...)` on scrollable content [EdgeInsets].
  static EdgeInsets footerScrollInsets(BuildContext context) =>
      EdgeInsets.only(bottom: footerScrollBottomPadding(context));
}
