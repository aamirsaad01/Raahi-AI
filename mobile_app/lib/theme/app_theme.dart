import 'package:flutter/material.dart';
import 'package:google_fonts/google_fonts.dart';

/// Material 3 theme for the Raahi AI app.
///
/// Style: **luxury minimal**.  Primary brand teal (`#1C6D83`) drives the
/// main surfaces, buttons, and nav; orange (`#EF7900`) is the accent for
/// FABs, highlights, and secondary actions.
///
/// Typography mixes a refined serif display face (`Playfair Display`)
/// with a clean, modern sans body face (`Plus Jakarta Sans`) – the
/// classic "editorial / boutique" pairing used by high-end travel
/// brands.
class AppTheme {
  const AppTheme._();

  /// Primary brand colour (teal — used as `ColorScheme.primary`).
  static const Color brandPrimary = Color(0xFF1C6D83);
  /// Accent orange (FAB, chips, secondary emphasis).
  static const Color brandOrange = Color(0xFFEF7900);

  static ThemeData light() => _build(Brightness.light);
  static ThemeData dark() => _build(Brightness.dark);

  static ThemeData _build(Brightness brightness) {
    final bool isDark = brightness == Brightness.dark;

    final ColorScheme base = ColorScheme.fromSeed(
      seedColor: brandPrimary,
      brightness: brightness,
    );

    final ColorScheme scheme = base.copyWith(
      primary: brandPrimary,
      onPrimary: Colors.white,
      primaryContainer: isDark
          ? const Color(0xFF2A8BA8)
          : const Color(0xFFD0E8EE),
      onPrimaryContainer: isDark ? const Color(0xFFE8F4F8) : const Color(0xFF0A3A47),
      secondary: brandOrange,
      onSecondary: Colors.white,
      secondaryContainer: isDark
          ? const Color(0xFFB85C00)
          : const Color(0xFFFFE0CC),
      onSecondaryContainer: isDark ? const Color(0xFFFFF4EC) : const Color(0xFF5C2E00),
      tertiary: brandOrange,
      onTertiary: Colors.white,
      // Warm off-white in light mode, deep ink in dark mode.
      surface: isDark ? const Color(0xFF0F1411) : const Color(0xFFF8F6F2),
      onSurface: isDark ? const Color(0xFFF2F0EA) : const Color(0xFF1B2226),
      surfaceContainerHighest:
          isDark ? const Color(0xFF1A2220) : const Color(0xFFEEEAE3),
      outlineVariant:
          isDark ? const Color(0xFF2C3431) : const Color(0xFFE0DBD2),
    );

    // Base body face.
    final TextTheme baseBody = GoogleFonts.plusJakartaSansTextTheme(
      isDark ? Typography.material2021().white : Typography.material2021().black,
    );
    // Display face (serif) for hero headlines only.
    final TextTheme baseDisplay = GoogleFonts.playfairDisplayTextTheme(baseBody);

    final TextTheme textTheme = baseBody.copyWith(
      displayLarge: baseDisplay.displayLarge?.copyWith(
        fontWeight: FontWeight.w600,
        letterSpacing: -0.5,
      ),
      displayMedium: baseDisplay.displayMedium?.copyWith(
        fontWeight: FontWeight.w600,
        letterSpacing: -0.4,
      ),
      displaySmall: baseDisplay.displaySmall?.copyWith(
        fontWeight: FontWeight.w600,
      ),
      headlineLarge: baseDisplay.headlineLarge?.copyWith(
        fontWeight: FontWeight.w600,
      ),
      headlineMedium: baseDisplay.headlineMedium?.copyWith(
        fontWeight: FontWeight.w600,
      ),
      titleLarge: baseBody.titleLarge?.copyWith(
        fontWeight: FontWeight.w700,
        letterSpacing: -0.2,
      ),
      titleMedium: baseBody.titleMedium?.copyWith(
        fontWeight: FontWeight.w600,
      ),
      labelLarge: baseBody.labelLarge?.copyWith(
        fontWeight: FontWeight.w600,
        letterSpacing: 0.2,
      ),
    );

    return ThemeData(
      useMaterial3: true,
      brightness: brightness,
      colorScheme: scheme,
      scaffoldBackgroundColor: scheme.surface,
      canvasColor: scheme.surface,
      textTheme: textTheme,
      primaryTextTheme: textTheme,

      appBarTheme: AppBarTheme(
        backgroundColor: scheme.surface,
        foregroundColor: scheme.onSurface,
        elevation: 0,
        scrolledUnderElevation: 0,
        centerTitle: true,
        titleTextStyle: textTheme.titleLarge?.copyWith(
          color: scheme.onSurface,
          fontWeight: FontWeight.w700,
        ),
        iconTheme: IconThemeData(color: scheme.onSurface),
        actionsIconTheme: IconThemeData(color: scheme.onSurface),
      ),

      cardTheme: CardThemeData(
        color: scheme.surfaceContainerHighest,
        surfaceTintColor: Colors.transparent,
        elevation: 0,
        // Small default vertical margin so stacked Cards (e.g. lists)
        // always have a consistent breathing room.  Pages that grid their
        // own cards still control spacing via `mainAxisSpacing`/padding.
        margin: const EdgeInsets.symmetric(vertical: 6),
        clipBehavior: Clip.antiAlias,
        shape: RoundedRectangleBorder(
          borderRadius: BorderRadius.circular(20),
          side: BorderSide(color: scheme.outlineVariant),
        ),
      ),

      filledButtonTheme: FilledButtonThemeData(
        style: FilledButton.styleFrom(
          backgroundColor: scheme.primary,
          foregroundColor: scheme.onPrimary,
          padding: const EdgeInsets.symmetric(horizontal: 22, vertical: 14),
          textStyle: textTheme.labelLarge,
          shape: const StadiumBorder(),
          elevation: 0,
        ),
      ),

      elevatedButtonTheme: ElevatedButtonThemeData(
        style: ElevatedButton.styleFrom(
          backgroundColor: scheme.primary,
          foregroundColor: scheme.onPrimary,
          padding: const EdgeInsets.symmetric(horizontal: 22, vertical: 14),
          textStyle: textTheme.labelLarge,
          shape: const StadiumBorder(),
          elevation: 0,
        ),
      ),

      outlinedButtonTheme: OutlinedButtonThemeData(
        style: OutlinedButton.styleFrom(
          foregroundColor: scheme.primary,
          side: BorderSide(color: scheme.outlineVariant),
          padding: const EdgeInsets.symmetric(horizontal: 22, vertical: 14),
          textStyle: textTheme.labelLarge,
          shape: const StadiumBorder(),
        ),
      ),

      textButtonTheme: TextButtonThemeData(
        style: TextButton.styleFrom(
          foregroundColor: scheme.primary,
          textStyle: textTheme.labelLarge,
        ),
      ),

      floatingActionButtonTheme: FloatingActionButtonThemeData(
        backgroundColor: scheme.secondary,
        foregroundColor: scheme.onSecondary,
        elevation: 0,
        focusElevation: 0,
        highlightElevation: 0,
        hoverElevation: 0,
      ),

      iconButtonTheme: IconButtonThemeData(
        style: IconButton.styleFrom(foregroundColor: scheme.onSurface),
      ),

      inputDecorationTheme: InputDecorationTheme(
        filled: true,
        fillColor: scheme.surfaceContainerHighest,
        contentPadding:
            const EdgeInsets.symmetric(horizontal: 16, vertical: 14),
        hintStyle: textTheme.bodyMedium?.copyWith(
          color: scheme.onSurface.withValues(alpha: 0.55),
        ),
        labelStyle: textTheme.bodyMedium?.copyWith(
          color: scheme.onSurface.withValues(alpha: 0.75),
        ),
        border: OutlineInputBorder(
          borderRadius: BorderRadius.circular(16),
          borderSide: BorderSide(color: scheme.outlineVariant),
        ),
        enabledBorder: OutlineInputBorder(
          borderRadius: BorderRadius.circular(16),
          borderSide: BorderSide(color: scheme.outlineVariant),
        ),
        focusedBorder: OutlineInputBorder(
          borderRadius: BorderRadius.circular(16),
          borderSide: BorderSide(color: scheme.primary, width: 1.5),
        ),
      ),

      dividerTheme: DividerThemeData(
        color: scheme.outlineVariant,
        thickness: 1,
        space: 1,
      ),

      chipTheme: ChipThemeData(
        side: BorderSide(color: scheme.outlineVariant),
        backgroundColor: Colors.transparent,
        selectedColor: scheme.primary.withValues(alpha: 0.12),
        labelStyle: textTheme.labelMedium,
        shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(20)),
        padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 8),
      ),

      switchTheme: SwitchThemeData(
        thumbColor: WidgetStateProperty.resolveWith((Set<WidgetState> states) {
          if (states.contains(WidgetState.selected)) return scheme.onPrimary;
          return scheme.outline;
        }),
        trackColor: WidgetStateProperty.resolveWith((Set<WidgetState> states) {
          if (states.contains(WidgetState.selected)) return scheme.primary;
          return scheme.surfaceContainerHighest;
        }),
        trackOutlineColor: WidgetStateProperty.all(scheme.outlineVariant),
      ),

      snackBarTheme: SnackBarThemeData(
        backgroundColor: scheme.inverseSurface,
        contentTextStyle: textTheme.bodyMedium?.copyWith(
          color: scheme.onInverseSurface,
        ),
        behavior: SnackBarBehavior.floating,
        shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(16)),
      ),

      listTileTheme: ListTileThemeData(
        iconColor: scheme.onSurface,
        textColor: scheme.onSurface,
        shape: RoundedRectangleBorder(
          borderRadius: BorderRadius.circular(16),
        ),
      ),

      dialogTheme: DialogThemeData(
        backgroundColor: scheme.surface,
        surfaceTintColor: Colors.transparent,
        shape: RoundedRectangleBorder(
          borderRadius: BorderRadius.circular(24),
        ),
      ),
    );
  }
}
