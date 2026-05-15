import 'dart:ui';

import 'package:flutter/material.dart';
import 'package:geolocator/geolocator.dart';
import 'package:url_launcher/url_launcher.dart';
import '../../routes/app_routes.dart';
import '../../utils/app_constants.dart';
import '../auth/auth_session.dart';
import 'emergency_contact_service.dart';

class EmergencyPage extends StatefulWidget {
  const EmergencyPage({super.key});

  @override
  State<EmergencyPage> createState() => _EmergencyPageState();
}

class _EmergencyPageState extends State<EmergencyPage> {
  final EmergencyContactService _contactService = EmergencyContactService();
  bool _sendingSos = false;

  Future<void> _handleOneTapSos() async {
    setState(() => _sendingSos = true);
    try {
      final sessionUser = await AuthSession.load();
      if (sessionUser == null) {
        throw Exception('Please login first to use SOS.');
      }
      final linked = await _contactService.getLatestLinkedForUser(sessionUser.userId);
      if (linked == null) {
        throw Exception(
          'No emergency contact found for your latest itinerary. '
          'Generate itinerary and save emergency contact first.',
        );
      }

      final pos = await _getLiveLocation();
      final lat = pos.latitude.toStringAsFixed(6);
      final lon = pos.longitude.toStringAsFixed(6);
      final mapsUrl = 'https://maps.google.com/?q=$lat,$lon';
      final msg = 'EMERGENCY: This is ${sessionUser.name}. I need urgent help.\n'
          'Last known location: $lat, $lon\n'
          'Google Maps: $mapsUrl';

      if (!mounted) return;
      await showModalBottomSheet<void>(
        context: context,
        showDragHandle: true,
        builder: (BuildContext context) {
          return Padding(
            padding: const EdgeInsets.all(16),
            child: Column(
              mainAxisSize: MainAxisSize.min,
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text('Emergency Numbers',
                    style: Theme.of(context).textTheme.titleMedium?.copyWith(
                          fontWeight: FontWeight.bold,
                        )),
                const SizedBox(height: 10),
                Wrap(
                  spacing: 8,
                  runSpacing: 8,
                  children: [
                    _numChip('Rescue 1122', '1122'),
                    _numChip('Police 15', '15'),
                    _numChip('Ambulance', '115'),
                  ],
                ),
                const SizedBox(height: 12),
                Text(
                  'Message Preview',
                  style: Theme.of(context).textTheme.labelLarge,
                ),
                const SizedBox(height: 6),
                Text(msg, style: Theme.of(context).textTheme.bodySmall),
                const SizedBox(height: 14),
                SizedBox(
                  width: double.infinity,
                  child: FilledButton.icon(
                    icon: const Icon(Icons.sms_outlined),
                    label: Text('Send SOS to ${linked.contactName}'),
                    onPressed: () async {
                      final smsUri = Uri(
                        scheme: 'sms',
                        path: linked.phoneNumber,
                        queryParameters: <String, String>{'body': msg},
                      );
                      final ok = await launchUrl(smsUri);
                      if (!ok && context.mounted) {
                        ScaffoldMessenger.of(context).showSnackBar(
                          const SnackBar(content: Text('Could not open SMS app.')),
                        );
                      }
                    },
                  ),
                ),
              ],
            ),
          );
        },
      );
    } catch (e) {
      if (!mounted) return;
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text(e.toString().replaceAll('Exception: ', ''))),
      );
    } finally {
      if (mounted) setState(() => _sendingSos = false);
    }
  }

  Widget _numChip(String label, String number) {
    return ActionChip(
      avatar: const Icon(Icons.call_outlined, size: 18),
      label: Text('$label ($number)'),
      onPressed: () async {
        final uri = Uri.parse('tel:$number');
        await launchUrl(uri);
      },
    );
  }

  Future<Position> _getLiveLocation() async {
    final enabled = await Geolocator.isLocationServiceEnabled();
    if (!enabled) throw Exception('Location service is disabled.');

    var permission = await Geolocator.checkPermission();
    if (permission == LocationPermission.denied) {
      permission = await Geolocator.requestPermission();
    }
    if (permission == LocationPermission.denied ||
        permission == LocationPermission.deniedForever) {
      throw Exception('Location permission denied.');
    }

    try {
      return await Geolocator.getCurrentPosition(
        locationSettings: const LocationSettings(
          accuracy: LocationAccuracy.high,
        ),
      ).timeout(const Duration(seconds: 12));
    } catch (_) {
      final last = await Geolocator.getLastKnownPosition();
      if (last != null) return last;
      rethrow;
    }
  }

  @override
  Widget build(BuildContext context) {
    final List<_CardLink> cards = <_CardLink>[
      _CardLink('Offline Downloads', Icons.download_rounded, AppRoutes.emergencyDownloads),
      _CardLink('Safe Points', Icons.place_rounded, AppRoutes.emergencySafePoints),
      _CardLink('Emergency Contacts', Icons.contact_phone_rounded, AppRoutes.emergencySosSetup),
    ];
    return Scaffold(
      appBar: AppBar(title: const Text('Emergency Mode')),
      body: Padding(
        padding: const EdgeInsets.all(16.0),
        child: Column(
          children: [
            Card(
              color: Colors.red.shade700,
              child: InkWell(
                onTap: _sendingSos ? null : _handleOneTapSos,
                borderRadius: BorderRadius.circular(12),
                child: Padding(
                  padding: const EdgeInsets.symmetric(vertical: 18, horizontal: 16),
                  child: Row(
                    children: [
                      const Icon(Icons.sos, color: Colors.white, size: 34),
                      const SizedBox(width: 12),
                      Expanded(
                        child: Text(
                          _sendingSos ? 'Preparing SOS...' : 'ONE-TAP SOS',
                          style: const TextStyle(
                            color: Colors.white,
                            fontWeight: FontWeight.bold,
                            fontSize: 20,
                          ),
                        ),
                      ),
                      const Icon(Icons.arrow_forward_ios, color: Colors.white),
                    ],
                  ),
                ),
              ),
            ),
            const SizedBox(height: 10),
            Expanded(
              child: GridView.builder(
                padding: AppConstants.footerScrollInsets(context),
                gridDelegate: const SliverGridDelegateWithFixedCrossAxisCount(
                  crossAxisCount: 2,
                  crossAxisSpacing: 12,
                  mainAxisSpacing: 12,
                  childAspectRatio: 1.1,
                ),
                itemCount: cards.length,
                itemBuilder: (BuildContext context, int i) {
                  return _EmergencyGlassTile(link: cards[i]);
                },
              ),
            ),
          ],
        ),
      ),
    );
  }
}

/// Same frosted-glass + teal rim treatment as homepage feature tiles.
class _EmergencyGlassTile extends StatelessWidget {
  final _CardLink link;

  const _EmergencyGlassTile({required this.link});

  @override
  Widget build(BuildContext context) {
    final ThemeData theme = Theme.of(context);
    final ColorScheme colors = theme.colorScheme;
    final TextTheme text = theme.textTheme;
    final bool isDark = theme.brightness == Brightness.dark;
    final BorderRadius borderRadius = BorderRadius.circular(20);

    final List<Color> glassFill = <Color>[
      Colors.white.withValues(alpha: isDark ? 0.055 : 0.16),
      Colors.white.withValues(alpha: isDark ? 0.02 : 0.06),
    ];
    final Color glassHighlight =
        Colors.white.withValues(alpha: isDark ? 0.07 : 0.22);
    final Color tileOutline =
        colors.primary.withValues(alpha: isDark ? 0.58 : 0.72);

    return DecoratedBox(
      decoration: BoxDecoration(
        borderRadius: borderRadius,
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
          borderRadius: borderRadius,
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
                  borderRadius: borderRadius,
                  splashColor: colors.primary.withValues(alpha: 0.12),
                  highlightColor: colors.onSurface.withValues(alpha: 0.05),
                  onTap: () {
                    Navigator.of(context).pushNamed(link.route);
                  },
                  child: Padding(
                    padding: const EdgeInsets.symmetric(
                      horizontal: 12,
                      vertical: 14,
                    ),
                    child: Column(
                      mainAxisAlignment: MainAxisAlignment.center,
                      children: <Widget>[
                        DecoratedBox(
                          decoration: BoxDecoration(
                            gradient: LinearGradient(
                              begin: Alignment.topLeft,
                              end: Alignment.bottomRight,
                              colors: <Color>[
                                colors.primary.withValues(alpha: 0.12),
                                colors.primary.withValues(alpha: 0.055),
                              ],
                            ),
                            borderRadius: BorderRadius.circular(14),
                            border: Border.all(
                              color: Colors.white.withValues(
                                alpha: isDark ? 0.16 : 0.36,
                              ),
                              width: 1,
                            ),
                          ),
                          child: SizedBox(
                            width: 52,
                            height: 52,
                            child: Center(
                              child: Icon(
                                link.icon,
                                size: 28,
                                color: colors.primary,
                              ),
                            ),
                          ),
                        ),
                        const SizedBox(height: 10),
                        Text(
                          link.title,
                          textAlign: TextAlign.center,
                          maxLines: 2,
                          overflow: TextOverflow.ellipsis,
                          style: text.titleSmall?.copyWith(
                            fontWeight: FontWeight.w700,
                            height: 1.2,
                          ),
                        ),
                      ],
                    ),
                  ),
                ),
              ),
              Positioned.fill(
                child: IgnorePointer(
                  child: DecoratedBox(
                    decoration: BoxDecoration(
                      borderRadius: borderRadius,
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
  }
}

class _CardLink {
  final String title;
  final IconData icon;
  final String route;
  const _CardLink(this.title, this.icon, this.route);
}


