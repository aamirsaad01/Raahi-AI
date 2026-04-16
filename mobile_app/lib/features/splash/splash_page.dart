import 'dart:async';
import 'package:flutter/material.dart';
import '../../routes/app_routes.dart';
import '../auth/auth_session.dart';

class SplashPage extends StatefulWidget {
  const SplashPage({super.key});

  @override
  State<SplashPage> createState() => _SplashPageState();
}

class _SplashPageState extends State<SplashPage> {
  @override
  void initState() {
    super.initState();
    Timer(const Duration(milliseconds: 1500), () async {
      if (!mounted) return;
      final user = await AuthSession.load();
      if (!mounted) return;
      Navigator.of(context).pushNamedAndRemoveUntil(
        user == null ? AppRoutes.login : AppRoutes.home,
        (Route<dynamic> r) => false,
      );
    });
  }

  @override
  Widget build(BuildContext context) {
    final ColorScheme colors = Theme.of(context).colorScheme;
    return Scaffold(
      backgroundColor: colors.primary,
      body: const Center(
        child: Text(
          'Raahi AI',
          style: TextStyle(
            color: Colors.white,
            fontWeight: FontWeight.w700,
            fontSize: 36,
            letterSpacing: 0.5,
          ),
        ),
      ),
    );
  }
}


