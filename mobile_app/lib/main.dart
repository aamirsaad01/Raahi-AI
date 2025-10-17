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
    return MaterialApp(
      title: 'Raahi AI',
      debugShowCheckedModeBanner: false,
      theme: AppTheme.light(),
      darkTheme: AppTheme.dark(),
      routes: AppRoutes.routes(),
      onGenerateRoute: AppRoutes.onGenerateRoute,
      initialRoute: AppRoutes.splash,
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
                active = FooterTab.emergency;
                break;
              case AppRoutes.groupChat:
                active = FooterTab.chat;
                break;
              case AppRoutes.aiChat:
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
                            Navigator.of(context).pushNamedAndRemoveUntil(AppRoutes.home, (Route<dynamic> r) => false);
                            break;
                          case FooterTab.itinerary:
                            Navigator.of(context).pushNamed(AppRoutes.itinerary);
                            break;
                          case FooterTab.packing:
                            Navigator.of(context).pushNamed(AppRoutes.packing);
                            break;
                          case FooterTab.hazards:
                            Navigator.of(context).pushNamed(AppRoutes.hazardMap);
                            break;
                          case FooterTab.emergency:
                            Navigator.of(context).pushNamed(AppRoutes.emergency);
                            break;
                          case FooterTab.chat:
                            Navigator.of(context).pushNamed(AppRoutes.groupChat);
                            break;
                          case FooterTab.ai:
                            Navigator.of(context).pushNamed(AppRoutes.aiChat);
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
