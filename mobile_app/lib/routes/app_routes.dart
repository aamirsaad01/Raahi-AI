import 'package:flutter/material.dart';
import '../features/home/home_page.dart';
import '../features/itinerary/itinerary_page.dart';
import '../features/itinerary/results_page.dart';
import '../features/itinerary/day_detail_page.dart';
import '../features/itinerary/poi_detail_page.dart';
import '../features/itinerary/cost_breakdown_page.dart';
import '../features/itinerary/routes_map_page.dart';
import '../features/itinerary/models.dart';
import '../features/packing/packing_page.dart';
import '../features/packing/results_page.dart';
import '../features/packing/edit_item_page.dart';
import '../features/packing/models.dart';
import '../features/packing/saved_checklists_page.dart';
import '../features/hazard/hazard_map_page.dart';
import '../features/emergency/emergency_page.dart';
import '../features/group_chat/group_chat_page.dart';
import '../features/ai_chat/ai_chat_page.dart';
import '../features/splash/splash_page.dart';

class AppRoutes {
  const AppRoutes._();

  static const String home = '/home';
  static const String splash = '/';
  static const String itinerary = '/itinerary';
  static const String itineraryResults = '/itinerary/results';
  static const String itineraryDay = '/itinerary/day';
  static const String itineraryPoi = '/itinerary/poi';
  static const String itineraryCost = '/itinerary/cost';
  static const String itineraryMap = '/itinerary/map';
  static const String packing = '/packing';
  static const String hazardMap = '/hazards';
  static const String emergency = '/emergency';
  static const String groupChat = '/group-chat';
  static const String aiChat = '/ai-chat';
  static const String packingResults = '/packing/results';
  static const String packingEdit = '/packing/edit';
  static const String packingSaved = '/packing/saved';

  static Map<String, WidgetBuilder> routes() {
    return <String, WidgetBuilder>{
      splash: (BuildContext context) => const SplashPage(),
      home: (BuildContext context) => const HomePage(),
      itinerary: (BuildContext context) => const ItineraryFormPage(),
      itineraryResults: (BuildContext context) {
        final Object? args = ModalRoute.of(context)?.settings.arguments;
        return ItineraryResultsPage(form: args as ItineraryFormData);
      },
      itineraryDay: (BuildContext context) {
        final Object? args = ModalRoute.of(context)?.settings.arguments;
        return DayDetailPage(day: args as DayPlan);
      },
      itineraryPoi: (BuildContext context) {
        final Object? args = ModalRoute.of(context)?.settings.arguments;
        return PoiDetailPage(poi: args as Poi);
      },
      itineraryCost: (BuildContext context) {
        final Object? args = ModalRoute.of(context)?.settings.arguments;
        return CostBreakdownPage(itinerary: args as TripItinerary);
      },
      itineraryMap: (BuildContext context) {
        final Object? args = ModalRoute.of(context)?.settings.arguments;
        return RoutesMapPage(itinerary: args as TripItinerary);
      },
      packing: (BuildContext context) => const PackingFormPage(),
      packingResults: (BuildContext context) {
        final Object? args = ModalRoute.of(context)?.settings.arguments;
        return PackingResultsPage(form: args as PackingFormData);
      },
      packingEdit: (BuildContext context) {
        final Object? args = ModalRoute.of(context)?.settings.arguments;
        return PackingEditItemPage(item: args as PackingItem);
      },
      packingSaved: (BuildContext context) => const SavedChecklistsPage(),
      hazardMap: (BuildContext context) => const HazardMapPage(),
      emergency: (BuildContext context) => const EmergencyPage(),
      groupChat: (BuildContext context) => const GroupChatPage(),
      aiChat: (BuildContext context) => const AiChatPage(),
    };
  }

  static Route<dynamic>? onGenerateRoute(RouteSettings settings) {
    final Map<String, WidgetBuilder> table = routes();
    final WidgetBuilder? builder = table[settings.name];
    if (builder == null) return null;
    return PageRouteBuilder<dynamic>(
      settings: settings,
      pageBuilder: (BuildContext context, Animation<double> animation, Animation<double> secondaryAnimation) => builder(context),
      transitionDuration: const Duration(milliseconds: 220),
      reverseTransitionDuration: const Duration(milliseconds: 200),
      transitionsBuilder: (BuildContext context, Animation<double> animation, Animation<double> secondaryAnimation, Widget child) {
        final Animation<double> fade = CurvedAnimation(parent: animation, curve: Curves.easeInOutCubic);
        final Animation<double> scale = Tween<double>(begin: 0.98, end: 1.0).animate(CurvedAnimation(parent: animation, curve: Curves.easeOutCubic));
        return FadeTransition(
          opacity: fade,
          child: ScaleTransition(scale: scale, child: child),
        );
      },
    );
  }
}



