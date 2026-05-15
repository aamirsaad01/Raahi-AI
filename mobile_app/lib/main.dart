import 'package:flutter/material.dart';
import 'theme/app_theme.dart';
import 'theme/theme_controller.dart';
import 'routes/app_routes.dart';
import 'widgets/app_footer_nav.dart';
import 'widgets/travel_ambient_background.dart';
import 'navigation/footer_route_observer.dart';

Future<void> main() async {
  WidgetsFlutterBinding.ensureInitialized();
  // Load persisted theme preference before the first frame so the user
  // never sees a flash of the wrong mode on launch.
  await ThemeController.instance.load();
  runApp(const MyApp());
}

class MyApp extends StatelessWidget {
  const MyApp({super.key});

  @override
  Widget build(BuildContext context) {
    final FooterRouteObserver footerObserver = FooterRouteObserver();
    final GlobalKey<NavigatorState> navKey = GlobalKey<NavigatorState>();
    return AnimatedBuilder(
      animation: ThemeController.instance,
      builder: (BuildContext context, _) => MaterialApp(
        title: 'Raahi AI',
        debugShowCheckedModeBanner: false,
        theme: AppTheme.light(),
        darkTheme: AppTheme.dark(),
        themeMode: ThemeController.instance.mode,
        // Route table is resolved only in [AppRoutes.onGenerateRoute] so every
        // named push uses one consistent (opaque) transition — avoids the
        // default [MaterialPageRoute] showing the previous screen through
        // transparent scaffolds for a frame.
        routes: const <String, WidgetBuilder>{},
        onGenerateRoute: AppRoutes.onGenerateRoute,
        initialRoute: AppRoutes.splash,
        navigatorKey: navKey,
        navigatorObservers: <NavigatorObserver>[footerObserver],
        builder: (BuildContext context, Widget? child) {
          FooterTab? active;
          return ValueListenableBuilder<String?>(
            valueListenable: footerObserver.currentRouteName,
            builder: (BuildContext context, String? routeName, Widget? _) {
              switch (routeName) {
                case AppRoutes.itinerary:
                case AppRoutes.itineraryResults:
                case AppRoutes.itineraryDay:
                case AppRoutes.itineraryPoi:
                case AppRoutes.itineraryCost:
                case AppRoutes.itineraryMap:
                  active = FooterTab.itinerary;
                  break;
                case AppRoutes.packing:
                case AppRoutes.packingResults:
                case AppRoutes.packingEdit:
                case AppRoutes.packingSaved:
                  active = FooterTab.packing;
                  break;
                case AppRoutes.hazardMap:
                  active = FooterTab.hazards;
                  break;
                case AppRoutes.emergency:
                case AppRoutes.emergencyDownloads:
                case AppRoutes.emergencySafePoints:
                case AppRoutes.emergencySosSetup:
                case AppRoutes.emergencyOutbox:
                case AppRoutes.emergencySettings:
                  active = FooterTab.emergency;
                  break;
                case AppRoutes.aiChat:
                case AppRoutes.aiChatHistory:
                case AppRoutes.aiChatSettings:
                  active = FooterTab.ai;
                  break;
                case AppRoutes.home:
                  active = null; // No footer on Home
                  break;
                default:
                  active = null; // e.g., Splash
              }

              final Size mq = MediaQuery.sizeOf(context);
              return LayoutBuilder(
                builder: (BuildContext context, BoxConstraints constraints) {
                  final double w = constraints.hasBoundedWidth
                      ? constraints.maxWidth
                      : mq.width;
                  final double h = constraints.hasBoundedHeight
                      ? constraints.maxHeight
                      : mq.height;
                  return SizedBox(
                    width: w.isFinite ? w : mq.width,
                    height: h.isFinite ? h : mq.height,
                    child: Stack(
                      clipBehavior: Clip.none,
                      fit: StackFit.expand,
                      children: <Widget>[
                        Positioned.fill(
                          child: ColoredBox(
                            color: Theme.of(context).colorScheme.surface,
                          ),
                        ),
                        const Positioned.fill(
                          child: TravelAmbientBackground(),
                        ),
                        if (child != null) child,
                        if (active != null)
                          Positioned(
                            left: 0,
                            right: 0,
                            bottom: 0,
                            child: AppFooterNav(
                              current: active!,
                              onTap: (FooterTab tab) {
                                switch (tab) {
                                  case FooterTab.home:
                                    navKey.currentState
                                        ?.pushNamedAndRemoveUntil(
                                      AppRoutes.home,
                                      (Route<dynamic> r) => false,
                                    );
                                    break;
                                  case FooterTab.itinerary:
                                    navKey.currentState
                                        ?.pushNamed(AppRoutes.itinerary);
                                    break;
                                  case FooterTab.packing:
                                    navKey.currentState
                                        ?.pushNamed(AppRoutes.packing);
                                    break;
                                  case FooterTab.hazards:
                                    navKey.currentState
                                        ?.pushNamed(AppRoutes.hazardMap);
                                    break;
                                  case FooterTab.emergency:
                                    navKey.currentState
                                        ?.pushNamed(AppRoutes.emergency);
                                    break;
                                  case FooterTab.ai:
                                    navKey.currentState
                                        ?.pushNamed(AppRoutes.aiChat);
                                    break;
                                }
                              },
                            ),
                          ),
                      ],
                    ),
                  );
                },
              );
            },
          );
        },
      ),
    );
  }
}
