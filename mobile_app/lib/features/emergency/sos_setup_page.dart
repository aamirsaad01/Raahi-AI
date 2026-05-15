import 'package:flutter/material.dart';
import '../../utils/app_constants.dart';
import '../auth/auth_session.dart';
import 'emergency_contact_service.dart';

class SosSetupPage extends StatefulWidget {
  const SosSetupPage({super.key});

  @override
  State<SosSetupPage> createState() => _SosSetupPageState();
}

class _SosSetupPageState extends State<SosSetupPage> {
  final EmergencyContactService _service = EmergencyContactService();
  bool _loading = true;
  String? _error;
  List<EmergencyContactRecord> _contacts = <EmergencyContactRecord>[];

  @override
  void initState() {
    super.initState();
    _loadContacts();
  }

  Future<void> _loadContacts() async {
    setState(() {
      _loading = true;
      _error = null;
    });
    try {
      final user = await AuthSession.load();
      if (user == null) {
        throw Exception('Please login to view emergency contacts.');
      }
      final contacts = await _service.getContactsForLatestItineraryForUser(user.userId);
      if (!mounted) return;
      setState(() => _contacts = contacts);
    } catch (e) {
      if (!mounted) return;
      setState(() => _error = e.toString().replaceFirst('Exception: ', ''));
    } finally {
      if (mounted) setState(() => _loading = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('Emergency Contacts')),
      body: _loading
          ? const Center(child: CircularProgressIndicator())
          : RefreshIndicator(
              onRefresh: _loadContacts,
              child: ListView(
                padding: EdgeInsets.all(16.0).add(AppConstants.footerScrollInsets(context)),
                children: <Widget>[
                  Text(
                    'Contacts from your latest itinerary',
                    style: Theme.of(context).textTheme.titleMedium,
                  ),
                  const SizedBox(height: 8),
                  if (_error != null)
                    Card(
                      child: Padding(
                        padding: const EdgeInsets.all(12),
                        child: Text(_error!),
                      ),
                    ),
                  if (_error == null && _contacts.isEmpty)
                    const Card(
                      child: Padding(
                        padding: EdgeInsets.all(12),
                        child: Text('No emergency contacts found for your latest itinerary.'),
                      ),
                    ),
                  ..._contacts.map(
                    (EmergencyContactRecord c) => Card(
                      child: ListTile(
                        leading: const Icon(Icons.contact_phone_rounded),
                        title: Text(c.contactName),
                        subtitle: Text('${c.relationship} • ${c.phoneNumber}'),
                      ),
                    ),
                  ),
                ],
              ),
            ),
    );
  }
}


