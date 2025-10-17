import 'package:flutter/material.dart';
import '../../widgets/app_footer_nav.dart';

class EmergencyPage extends StatelessWidget {
  const EmergencyPage({super.key});

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('Emergency Mode')),
      body: const Center(child: Text('Emergency dashboard coming soon.')),
    );
  }
}


