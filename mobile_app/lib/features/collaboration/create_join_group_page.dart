import 'package:flutter/material.dart';
import '../../routes/app_routes.dart';
import 'models.dart';

class CreateJoinGroupPage extends StatefulWidget {
  final bool isCreating;
  const CreateJoinGroupPage({super.key, required this.isCreating});

  @override
  State<CreateJoinGroupPage> createState() => _CreateJoinGroupPageState();
}

class _CreateJoinGroupPageState extends State<CreateJoinGroupPage> {
  final TextEditingController _name = TextEditingController();
  final TextEditingController _code = TextEditingController();
  DateTime? _startDate;
  DateTime? _endDate;

  @override
  void dispose() {
    _name.dispose();
    _code.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: Text(widget.isCreating ? 'Create Group' : 'Join Group')),
      body: Padding(
        padding: const EdgeInsets.all(16.0),
        child: Column(
          children: <Widget>[
            if (widget.isCreating) ...<Widget>[
              TextField(
                controller: _name,
                decoration: const InputDecoration(labelText: 'Trip Name', border: OutlineInputBorder()),
              ),
              const SizedBox(height: 12),
              ListTile(
                title: Text(_startDate == null ? 'Start Date' : _startDate.toString().substring(0, 10)),
                trailing: const Icon(Icons.calendar_today_rounded),
                onTap: () async {
                  final DateTime? picked = await showDatePicker(context: context, firstDate: DateTime.now(), lastDate: DateTime.now().add(const Duration(days: 365)));
                  if (picked != null) setState(() => _startDate = picked);
                },
              ),
              ListTile(
                title: Text(_endDate == null ? 'End Date' : _endDate.toString().substring(0, 10)),
                trailing: const Icon(Icons.calendar_today_rounded),
                onTap: () async {
                  final DateTime? picked = await showDatePicker(context: context, firstDate: _startDate ?? DateTime.now(), lastDate: DateTime.now().add(const Duration(days: 365)));
                  if (picked != null) setState(() => _endDate = picked);
                },
              ),
            ] else
              TextField(
                controller: _code,
                decoration: const InputDecoration(labelText: 'Invite Code', border: OutlineInputBorder()),
              ),
            const SizedBox(height: 24),
            SizedBox(
              width: double.infinity,
              child: FilledButton.icon(
                onPressed: () {
                  if (widget.isCreating) {
                    if (_name.text.trim().isEmpty || _startDate == null || _endDate == null) {
                      ScaffoldMessenger.of(context).showSnackBar(const SnackBar(content: Text('Please fill all fields')));
                      return;
                    }
                  } else {
                    if (_code.text.trim().isEmpty) {
                      ScaffoldMessenger.of(context).showSnackBar(const SnackBar(content: Text('Please enter invite code')));
                      return;
                    }
                  }
                  ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text(widget.isCreating ? 'Group created (stub)' : 'Joined group (stub)')));
                  Navigator.of(context).pop();
                },
                icon: Icon(widget.isCreating ? Icons.add_rounded : Icons.group_add_rounded),
                label: Text(widget.isCreating ? 'Create Group' : 'Join Group'),
              ),
            ),
            const SizedBox(height: 60),
          ],
        ),
      ),
    );
  }
}

