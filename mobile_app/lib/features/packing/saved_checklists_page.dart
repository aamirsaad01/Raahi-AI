import 'package:flutter/material.dart';
import '../../widgets/app_footer_nav.dart';

class SavedChecklistsPage extends StatelessWidget {
  const SavedChecklistsPage({super.key});

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('Saved Checklists')),
      body: const Center(
        child: Text('No saved checklists yet.'),
      ),
    );
  }
}


