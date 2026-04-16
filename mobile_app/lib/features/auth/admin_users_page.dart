import 'package:flutter/material.dart';

import 'auth_service.dart';
import 'auth_session.dart';
import 'models.dart';

class AdminUsersPage extends StatefulWidget {
  const AdminUsersPage({super.key});

  @override
  State<AdminUsersPage> createState() => _AdminUsersPageState();
}

class _AdminUsersPageState extends State<AdminUsersPage> {
  final AuthService _service = AuthService();
  List<AuthUser> _users = <AuthUser>[];
  bool _loading = true;
  String _adminEmail = '';

  @override
  void initState() {
    super.initState();
    _load();
  }

  Future<void> _load() async {
    setState(() => _loading = true);
    try {
      final me = await AuthSession.load();
      if (me == null || !me.isAdmin) {
        throw Exception('Admin login required');
      }
      _adminEmail = me.email;
      final users = await _service.getAllUsers(adminEmail: _adminEmail);
      if (!mounted) return;
      setState(() => _users = users);
    } catch (e) {
      if (!mounted) return;
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text(e.toString().replaceFirst('Exception: ', ''))),
      );
    } finally {
      if (mounted) setState(() => _loading = false);
    }
  }

  Future<void> _toggleActive(AuthUser user, bool value) async {
    try {
      await _service.updateUser(
        userId: user.userId,
        adminEmail: _adminEmail,
        updates: <String, dynamic>{'is_active': value},
      );
      await _load();
    } catch (e) {
      if (!mounted) return;
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text(e.toString().replaceFirst('Exception: ', ''))),
      );
    }
  }

  Future<void> _delete(AuthUser user) async {
    final yes = await showDialog<bool>(
      context: context,
      builder: (BuildContext context) => AlertDialog(
        title: const Text('Delete user'),
        content: Text('Delete ${user.email} and related data?'),
        actions: <Widget>[
          TextButton(
            onPressed: () => Navigator.pop(context, false),
            child: const Text('Cancel'),
          ),
          FilledButton(
            onPressed: () => Navigator.pop(context, true),
            child: const Text('Delete'),
          ),
        ],
      ),
    );
    if (yes != true) return;
    try {
      await _service.deleteUser(userId: user.userId, adminEmail: _adminEmail);
      await _load();
    } catch (e) {
      if (!mounted) return;
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text(e.toString().replaceFirst('Exception: ', ''))),
      );
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('Admin - Users'),
        actions: <Widget>[
          IconButton(onPressed: _load, icon: const Icon(Icons.refresh)),
        ],
      ),
      body: _loading
          ? const Center(child: CircularProgressIndicator())
          : ListView.separated(
              itemCount: _users.length,
              separatorBuilder: (_, __) => const Divider(height: 1),
              itemBuilder: (BuildContext context, int i) {
                final u = _users[i];
                return ListTile(
                  title: Text('${u.name} (${u.email})'),
                  subtitle: Text(
                    'CNIC: ${u.cnic}\nContact: ${u.contactNumber}\n'
                    'Role: ${u.isAdmin ? 'Admin' : 'User'}',
                  ),
                  isThreeLine: true,
                  trailing: Row(
                    mainAxisSize: MainAxisSize.min,
                    children: <Widget>[
                      Switch(
                        value: u.isActive,
                        onChanged: u.isAdmin ? null : (v) => _toggleActive(u, v),
                      ),
                      IconButton(
                        onPressed: u.isAdmin ? null : () => _delete(u),
                        icon: const Icon(Icons.delete_outline),
                      ),
                    ],
                  ),
                );
              },
            ),
    );
  }
}

