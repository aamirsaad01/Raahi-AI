import 'package:flutter/material.dart';

import '../../routes/app_routes.dart';
import '../../theme/theme_controller.dart';
import '../auth/auth_session.dart';

/// App-wide settings: appearance + account.
///
/// The appearance section drives [ThemeController] which is wired into
/// `MaterialApp.themeMode` in `main.dart`, so toggling here updates the
/// entire app instantly and the preference survives restart.
class AppSettingsPage extends StatefulWidget {
  const AppSettingsPage({super.key});

  @override
  State<AppSettingsPage> createState() => _AppSettingsPageState();
}

class _AppSettingsPageState extends State<AppSettingsPage> {
  Future<void> _logout() async {
    await AuthSession.clear();
    if (!mounted) return;
    Navigator.of(context).pushNamedAndRemoveUntil(
      AppRoutes.login,
      (Route<dynamic> r) => false,
    );
  }

  @override
  Widget build(BuildContext context) {
    final ThemeData theme = Theme.of(context);
    final ColorScheme colors = theme.colorScheme;
    final TextTheme text = theme.textTheme;

    return AnimatedBuilder(
      animation: ThemeController.instance,
      builder: (BuildContext context, _) {
        final ThemeMode mode = ThemeController.instance.mode;
        return Scaffold(
          appBar: AppBar(
            title: const Text('Settings'),
            leading: IconButton(
              icon: const Icon(Icons.arrow_back_ios_new_rounded),
              onPressed: () => Navigator.of(context).maybePop(),
            ),
          ),
          body: ListView(
            padding: const EdgeInsets.fromLTRB(20, 8, 20, 24),
            children: <Widget>[
              _SectionLabel(text: 'Appearance'),
              const SizedBox(height: 10),
              _SettingsCard(
                child: Column(
                  children: <Widget>[
                    SwitchListTile.adaptive(
                      value: mode == ThemeMode.dark,
                      onChanged: (bool v) =>
                          ThemeController.instance.toggleDark(v),
                      title: Text(
                        'Dark mode',
                        style: text.titleMedium,
                      ),
                      subtitle: Text(
                        mode == ThemeMode.dark
                            ? 'On — Raahi will use a darker palette.'
                            : 'Off — Raahi will use a light, warm palette.',
                        style: text.bodySmall?.copyWith(
                          color: colors.onSurface.withValues(alpha: 0.7),
                        ),
                      ),
                      secondary: _IconBubble(
                        icon: mode == ThemeMode.dark
                            ? Icons.dark_mode_rounded
                            : Icons.light_mode_rounded,
                      ),
                      contentPadding: const EdgeInsets.symmetric(
                        horizontal: 16,
                        vertical: 6,
                      ),
                    ),
                    Divider(
                      height: 1,
                      color: colors.outlineVariant,
                    ),
                    ListTile(
                      contentPadding: const EdgeInsets.symmetric(
                        horizontal: 16,
                        vertical: 6,
                      ),
                      leading: _IconBubble(
                        icon: Icons.settings_suggest_rounded,
                      ),
                      title: Text('Match system', style: text.titleMedium),
                      subtitle: Text(
                        mode == ThemeMode.system
                            ? 'On — follows your phone\'s theme.'
                            : 'Off — using your manual choice.',
                        style: text.bodySmall?.copyWith(
                          color: colors.onSurface.withValues(alpha: 0.7),
                        ),
                      ),
                      trailing: Switch.adaptive(
                        value: mode == ThemeMode.system,
                        onChanged: (bool v) {
                          if (v) {
                            ThemeController.instance.setMode(ThemeMode.system);
                          } else {
                            // Fall back to a sensible explicit mode.
                            ThemeController.instance.setMode(
                              MediaQuery.platformBrightnessOf(context) ==
                                      Brightness.dark
                                  ? ThemeMode.dark
                                  : ThemeMode.light,
                            );
                          }
                        },
                      ),
                    ),
                  ],
                ),
              ),
              const SizedBox(height: 24),
              _SectionLabel(text: 'Account'),
              const SizedBox(height: 10),
              _SettingsCard(
                child: ListTile(
                  contentPadding: const EdgeInsets.symmetric(
                    horizontal: 16,
                    vertical: 6,
                  ),
                  leading: _IconBubble(
                    icon: Icons.logout_rounded,
                    tone: colors.error,
                  ),
                  title: Text(
                    'Log out',
                    style: text.titleMedium?.copyWith(color: colors.error),
                  ),
                  subtitle: Text(
                    'Sign out of this device.',
                    style: text.bodySmall?.copyWith(
                      color: colors.onSurface.withValues(alpha: 0.7),
                    ),
                  ),
                  trailing: Icon(
                    Icons.chevron_right_rounded,
                    color: colors.onSurface.withValues(alpha: 0.6),
                  ),
                  onTap: _logout,
                ),
              ),
              const SizedBox(height: 28),
              Center(
                child: Text(
                  'Raahi AI · v1.0',
                  style: text.labelSmall?.copyWith(
                    color: colors.onSurface.withValues(alpha: 0.5),
                    letterSpacing: 0.8,
                  ),
                ),
              ),
            ],
          ),
        );
      },
    );
  }
}

class _SectionLabel extends StatelessWidget {
  final String text;
  const _SectionLabel({required this.text});

  @override
  Widget build(BuildContext context) {
    final ColorScheme colors = Theme.of(context).colorScheme;
    return Padding(
      padding: const EdgeInsets.only(left: 4),
      child: Text(
        text.toUpperCase(),
        style: Theme.of(context).textTheme.labelMedium?.copyWith(
              color: colors.onSurface.withValues(alpha: 0.6),
              letterSpacing: 1.4,
              fontWeight: FontWeight.w600,
            ),
      ),
    );
  }
}

class _SettingsCard extends StatelessWidget {
  final Widget child;
  const _SettingsCard({required this.child});

  @override
  Widget build(BuildContext context) {
    final ColorScheme colors = Theme.of(context).colorScheme;
    return Container(
      decoration: BoxDecoration(
        color: colors.surfaceContainerHighest,
        borderRadius: BorderRadius.circular(20),
        border: Border.all(color: colors.outlineVariant),
      ),
      child: child,
    );
  }
}

class _IconBubble extends StatelessWidget {
  final IconData icon;
  final Color? tone;
  const _IconBubble({required this.icon, this.tone});

  @override
  Widget build(BuildContext context) {
    final ColorScheme colors = Theme.of(context).colorScheme;
    final Color colour = tone ?? colors.primary;
    return Container(
      width: 40,
      height: 40,
      decoration: BoxDecoration(
        color: colour.withValues(alpha: 0.12),
        shape: BoxShape.circle,
      ),
      alignment: Alignment.center,
      child: Icon(icon, color: colour, size: 20),
    );
  }
}
