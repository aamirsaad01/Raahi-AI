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
import '../features/hazard/report_hazard_page.dart';
import '../features/hazard/my_reports_page.dart';
import '../features/emergency/emergency_page.dart';
import '../features/emergency/downloads_page.dart';
import '../features/emergency/safe_points_page.dart';
import '../features/emergency/sos_setup_page.dart';
import '../features/emergency/outbox_page.dart';
import '../features/emergency/settings_page.dart';
import '../features/collaboration/groups_list_page.dart';
import '../features/collaboration/create_join_group_page.dart';
import '../features/collaboration/chat_room_page.dart';
import '../features/collaboration/members_page.dart';
import '../features/collaboration/map_page.dart';
import '../features/collaboration/expenses_page.dart';
import '../features/collaboration/add_expense_page.dart';
import '../features/collaboration/photos_page.dart';
import '../features/collaboration/polls_page.dart';
import '../features/collaboration/create_poll_page.dart';
import '../features/collaboration/models.dart';
import '../features/ai_chat/ai_chat_page.dart';
import '../features/ai_chat/history_page.dart';
import '../features/ai_chat/settings_page.dart';
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
  static const String hazardReport = '/hazards/report';
  static const String hazardMyReports = '/hazards/mine';
  static const String emergency = '/emergency';
  static const String emergencyDownloads = '/emergency/downloads';
  static const String emergencySafePoints = '/emergency/safe';
  static const String emergencySosSetup = '/emergency/sos';
  static const String emergencyOutbox = '/emergency/outbox';
  static const String emergencySettings = '/emergency/settings';
  static const String collaboration = '/collaboration';
  static const String collaborationCreate = '/collaboration/create';
  static const String collaborationJoin = '/collaboration/join';
  static const String collaborationChat = '/collaboration/chat';
  static const String collaborationMembers = '/collaboration/members';
  static const String collaborationMap = '/collaboration/map';
  static const String collaborationExpenses = '/collaboration/expenses';
  static const String collaborationExpenseAdd = '/collaboration/expense/add';
  static const String collaborationPhotos = '/collaboration/photos';
  static const String collaborationPolls = '/collaboration/polls';
  static const String collaborationPollCreate = '/collaboration/poll/create';
  static const String aiChat = '/ai-chat';
  static const String aiChatHistory = '/ai-chat/history';
  static const String aiChatSettings = '/ai-chat/settings';
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
      hazardReport: (BuildContext context) => const ReportHazardPage(),
      hazardMyReports: (BuildContext context) => const MyReportsPage(),
      emergency: (BuildContext context) => const EmergencyPage(),
      emergencyDownloads: (BuildContext context) => const EmergencyDownloadsPage(),
      emergencySafePoints: (BuildContext context) => const SafePointsPage(),
      emergencySosSetup: (BuildContext context) => const SosSetupPage(),
      emergencyOutbox: (BuildContext context) => const EmergencyOutboxPage(),
      emergencySettings: (BuildContext context) => const EmergencySettingsPage(),
      collaboration: (BuildContext context) => const GroupsListPage(),
      collaborationCreate: (BuildContext context) => const CreateJoinGroupPage(isCreating: true),
      collaborationJoin: (BuildContext context) => const CreateJoinGroupPage(isCreating: false),
      collaborationChat: (BuildContext context) {
        final Object? args = ModalRoute.of(context)?.settings.arguments;
        return ChatRoomPage(group: args as TripGroup);
      },
      collaborationMembers: (BuildContext context) => const MembersPage(),
      collaborationMap: (BuildContext context) => const CollaborationMapPage(),
      collaborationExpenses: (BuildContext context) => const ExpensesPage(),
      collaborationExpenseAdd: (BuildContext context) => const AddExpensePage(),
      collaborationPhotos: (BuildContext context) => const PhotosPage(),
      collaborationPolls: (BuildContext context) => const PollsPage(),
      collaborationPollCreate: (BuildContext context) => const CreatePollPage(),
      aiChat: (BuildContext context) => const AiChatPage(),
      aiChatHistory: (BuildContext context) => const AiChatHistoryPage(),
      aiChatSettings: (BuildContext context) => const AiChatSettingsPage(),
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



