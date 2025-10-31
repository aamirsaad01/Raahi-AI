import 'package:flutter/material.dart';

class FooterRouteObserver extends NavigatorObserver {
  final ValueNotifier<String?> currentRouteName = ValueNotifier<String?>(null);

  void _update(Route<dynamic>? route) {
    final String? name = route?.settings.name;
    if (currentRouteName.value == name) return;
    WidgetsBinding.instance.addPostFrameCallback((Duration _) {
      if (currentRouteName.value != name) {
        currentRouteName.value = name;
      }
    });
  }

  @override
  void didPush(Route<dynamic> route, Route<dynamic>? previousRoute) {
    super.didPush(route, previousRoute);
    _update(route);
  }

  @override
  void didPop(Route<dynamic> route, Route<dynamic>? previousRoute) {
    super.didPop(route, previousRoute);
    _update(previousRoute);
  }

  @override
  void didReplace({Route<dynamic>? newRoute, Route<dynamic>? oldRoute}) {
    super.didReplace(newRoute: newRoute, oldRoute: oldRoute);
    _update(newRoute);
  }
}


