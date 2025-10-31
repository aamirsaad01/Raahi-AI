import 'package:flutter/material.dart';
import 'theme/app_theme.dart';
import 'routes/app_routes.dart';
import 'widgets/app_footer_nav.dart';
import 'navigation/footer_route_observer.dart';

void main() {
  runApp(const MyApp());
}

class MyApp extends StatelessWidget {
  const MyApp({super.key});

  @override
  Widget build(BuildContext context) {
    final FooterRouteObserver footerObserver = FooterRouteObserver();
    final GlobalKey<NavigatorState> navKey = GlobalKey<NavigatorState>();
    return MaterialApp(
      title: 'Raahi AI',
      debugShowCheckedModeBanner: false,
      theme: AppTheme.light(),
      darkTheme: AppTheme.dark(),
      routes: AppRoutes.routes(),
      onGenerateRoute: AppRoutes.onGenerateRoute,
      initialRoute: AppRoutes.splash,
      navigatorKey: navKey,
      navigatorObservers: <NavigatorObserver>[footerObserver],
      builder: (BuildContext context, Widget? child) {
        // Derive current tab from route name
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
              case AppRoutes.collaboration:
              case AppRoutes.collaborationCreate:
              case AppRoutes.collaborationJoin:
              case AppRoutes.collaborationChat:
              case AppRoutes.collaborationMembers:
              case AppRoutes.collaborationMap:
              case AppRoutes.collaborationExpenses:
              case AppRoutes.collaborationExpenseAdd:
              case AppRoutes.collaborationPhotos:
              case AppRoutes.collaborationPolls:
              case AppRoutes.collaborationPollCreate:
                active = FooterTab.chat;
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

            return Stack(
              children: <Widget>[
                if (child != null) child,
                if (active != null)
                  Align(
                    alignment: Alignment.bottomCenter,
                    child: AppFooterNav(
                      current: active,
                      onTap: (FooterTab tab) {
                        // Delegate to default navigation behavior
                        switch (tab) {
                          case FooterTab.home:
                            navKey.currentState?.pushNamedAndRemoveUntil(AppRoutes.home, (Route<dynamic> r) => false);
                            break;
                          case FooterTab.itinerary:
                            navKey.currentState?.pushNamed(AppRoutes.itinerary);
                            break;
                          case FooterTab.packing:
                            navKey.currentState?.pushNamed(AppRoutes.packing);
                            break;
                          case FooterTab.hazards:
                            navKey.currentState?.pushNamed(AppRoutes.hazardMap);
                            break;
                          case FooterTab.emergency:
                            navKey.currentState?.pushNamed(AppRoutes.emergency);
                            break;
                          case FooterTab.chat:
                            navKey.currentState?.pushNamed(AppRoutes.collaboration);
                            break;
                          case FooterTab.ai:
                            navKey.currentState?.pushNamed(AppRoutes.aiChat);
                            break;
                        }
                      },
                    ),
                  ),
              ],
            );
          },
        );
      },
    );
  }
}
