import 'package:flutter/material.dart';

/// App-wide constants
class AppConstants {
  /// Footer navigation height including SafeArea padding
  /// This accounts for the footer height so content doesn't get hidden behind it
  static const double footerHeight = 80.0;
  
  /// Bottom padding to add to scrollable content to prevent footer overlap
  static const EdgeInsets footerPadding = EdgeInsets.only(bottom: 80.0);
}

