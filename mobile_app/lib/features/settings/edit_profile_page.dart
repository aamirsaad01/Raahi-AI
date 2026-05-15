import 'package:flutter/material.dart';

import '../../routes/app_routes.dart';
import '../auth/auth_service.dart';
import '../auth/auth_session.dart';
import '../auth/models.dart';

/// Edit profile fields collected at signup (name, contact, DOB, CNIC, etc.).
///
/// Requires the account password to apply changes. Optional new email /
/// new password are sent to [AuthService.updateMyProfile] and the session
/// is refreshed from the returned user.
class EditProfilePage extends StatefulWidget {
  const EditProfilePage({super.key});

  @override
  State<EditProfilePage> createState() => _EditProfilePageState();
}

class _EditProfilePageState extends State<EditProfilePage> {
  final GlobalKey<FormState> _formKey = GlobalKey<FormState>();
  final TextEditingController _nameCtrl = TextEditingController();
  final TextEditingController _emailCtrl = TextEditingController();
  final TextEditingController _newEmailCtrl = TextEditingController();
  final TextEditingController _contactCtrl = TextEditingController();
  final TextEditingController _dobCtrl = TextEditingController();
  final TextEditingController _cnicCtrl = TextEditingController();
  final TextEditingController _medicalCtrl = TextEditingController();
  final TextEditingController _currentPwdCtrl = TextEditingController();
  final TextEditingController _newPwdCtrl = TextEditingController();
  final TextEditingController _confirmPwdCtrl = TextEditingController();

  AuthUser? _user;
  bool _loading = true;
  bool _saving = false;
  String? _loadError;

  @override
  void initState() {
    super.initState();
    _loadUser();
  }

  Future<void> _loadUser() async {
    final AuthUser? u = await AuthSession.load();
    if (!mounted) return;
    if (u == null) {
      setState(() {
        _loading = false;
        _loadError = 'You need to be logged in to edit your profile.';
      });
      return;
    }
    setState(() {
      _user = u;
      _nameCtrl.text = u.name;
      _emailCtrl.text = u.email;
      _contactCtrl.text = u.contactNumber;
      _dobCtrl.text = u.dob;
      _cnicCtrl.text = u.cnic;
      _medicalCtrl.text = u.medicalConditions;
      _loading = false;
    });
  }

  @override
  void dispose() {
    _nameCtrl.dispose();
    _emailCtrl.dispose();
    _newEmailCtrl.dispose();
    _contactCtrl.dispose();
    _dobCtrl.dispose();
    _cnicCtrl.dispose();
    _medicalCtrl.dispose();
    _currentPwdCtrl.dispose();
    _newPwdCtrl.dispose();
    _confirmPwdCtrl.dispose();
    super.dispose();
  }

  Future<void> _save() async {
    if (_user == null) return;
    if (!_formKey.currentState!.validate()) return;

    final String newEmail = _newEmailCtrl.text.trim();
    final String newPwd = _newPwdCtrl.text;
    final String confirm = _confirmPwdCtrl.text;
    if (newPwd.isNotEmpty && newPwd != confirm) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('New password and confirmation do not match.')),
      );
      return;
    }

    setState(() => _saving = true);
    try {
      final AuthUser updated = await AuthService().updateMyProfile(
        email: _user!.email,
        currentPassword: _currentPwdCtrl.text,
        name: _nameCtrl.text,
        contactNumber: _contactCtrl.text,
        dob: _dobCtrl.text,
        cnic: _cnicCtrl.text,
        medicalConditions: _medicalCtrl.text,
        newEmail: newEmail.isEmpty ? null : newEmail,
        newPassword: newPwd.isEmpty ? null : newPwd,
      );
      await AuthSession.save(updated);
      if (!mounted) return;
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('Profile updated')),
      );
      Navigator.of(context).pop();
    } catch (e) {
      if (!mounted) return;
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text(e.toString().replaceFirst('Exception: ', ''))),
      );
    } finally {
      if (mounted) setState(() => _saving = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    final ThemeData theme = Theme.of(context);
    final ColorScheme colors = theme.colorScheme;
    final TextTheme text = theme.textTheme;

    if (_loading) {
      return Scaffold(
        appBar: AppBar(title: const Text('Personal information')),
        body: const Center(child: CircularProgressIndicator()),
      );
    }

    if (_loadError != null) {
      return Scaffold(
        appBar: AppBar(title: const Text('Personal information')),
        body: Center(
          child: Padding(
            padding: const EdgeInsets.all(24),
            child: Column(
              mainAxisSize: MainAxisSize.min,
              children: <Widget>[
                Text(_loadError!, textAlign: TextAlign.center),
                const SizedBox(height: 16),
                FilledButton(
                  onPressed: () =>
                      Navigator.of(context).pushNamedAndRemoveUntil(
                    AppRoutes.login,
                    (Route<dynamic> r) => false,
                  ),
                  child: const Text('Go to login'),
                ),
              ],
            ),
          ),
        ),
      );
    }

    return Scaffold(
      appBar: AppBar(
        title: const Text('Personal information'),
        leading: IconButton(
          icon: const Icon(Icons.arrow_back_ios_new_rounded),
          onPressed: () => Navigator.of(context).maybePop(),
        ),
      ),
      body: SingleChildScrollView(
        padding: const EdgeInsets.fromLTRB(20, 12, 20, 32),
        child: Form(
          key: _formKey,
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.stretch,
            children: <Widget>[
              Text(
                'Update the details you used when creating your account. '
                'Your current password is required to save changes.',
                style: text.bodyMedium?.copyWith(
                  color: colors.onSurface.withValues(alpha: 0.72),
                ),
              ),
              const SizedBox(height: 20),
              TextFormField(
                controller: _nameCtrl,
                decoration: const InputDecoration(labelText: 'Name'),
                textCapitalization: TextCapitalization.words,
                validator: (String? v) {
                  if (v == null || v.trim().length < 2) return 'Name required';
                  return null;
                },
              ),
              const SizedBox(height: 12),
              TextFormField(
                controller: _emailCtrl,
                readOnly: true,
                decoration: const InputDecoration(
                  labelText: 'Current email',
                  helperText: 'Use “New email” below if you want to change it',
                ),
              ),
              const SizedBox(height: 12),
              TextFormField(
                controller: _newEmailCtrl,
                decoration: const InputDecoration(
                  labelText: 'New email (optional)',
                ),
                keyboardType: TextInputType.emailAddress,
                validator: (String? v) {
                  final String s = v?.trim() ?? '';
                  if (s.isEmpty) return null;
                  if (!s.contains('@')) return 'Enter a valid email';
                  return null;
                },
              ),
              const SizedBox(height: 12),
              TextFormField(
                controller: _contactCtrl,
                decoration: const InputDecoration(labelText: 'Contact number'),
                keyboardType: TextInputType.phone,
                validator: (String? v) {
                  if (v == null || v.trim().length < 10) {
                    return 'Valid contact required (10–15 digits)';
                  }
                  return null;
                },
              ),
              const SizedBox(height: 12),
              TextFormField(
                controller: _dobCtrl,
                decoration: const InputDecoration(
                  labelText: 'Date of birth (YYYY-MM-DD)',
                ),
                validator: (String? v) =>
                    (v == null || v.trim().isEmpty) ? 'DOB required' : null,
              ),
              const SizedBox(height: 12),
              TextFormField(
                controller: _cnicCtrl,
                decoration: const InputDecoration(
                  labelText: 'CNIC (12345-1234567-1)',
                ),
                validator: (String? v) {
                  if (v == null || v.trim().isEmpty) return 'CNIC required';
                  final RegExp re = RegExp(r'^\d{5}-\d{7}-\d$');
                  if (!re.hasMatch(v.trim())) {
                    return 'Use format 12345-1234567-1';
                  }
                  return null;
                },
              ),
              const SizedBox(height: 12),
              TextFormField(
                controller: _medicalCtrl,
                decoration: const InputDecoration(
                  labelText: 'Medical conditions (optional)',
                ),
                maxLines: 2,
              ),
              const SizedBox(height: 20),
              Text(
                'Change password (optional)',
                style: text.titleSmall?.copyWith(fontWeight: FontWeight.w600),
              ),
              const SizedBox(height: 8),
              TextFormField(
                controller: _newPwdCtrl,
                obscureText: true,
                decoration: const InputDecoration(
                  labelText: 'New password',
                  helperText: 'Leave blank to keep your current password',
                ),
              ),
              const SizedBox(height: 12),
              TextFormField(
                controller: _confirmPwdCtrl,
                obscureText: true,
                decoration: const InputDecoration(
                  labelText: 'Confirm new password',
                ),
              ),
              const SizedBox(height: 24),
              Text(
                'Confirm it’s you',
                style: text.titleSmall?.copyWith(fontWeight: FontWeight.w600),
              ),
              const SizedBox(height: 8),
              TextFormField(
                controller: _currentPwdCtrl,
                obscureText: true,
                decoration: const InputDecoration(
                  labelText: 'Current password',
                ),
                validator: (String? v) {
                  if (v == null || v.isEmpty) {
                    return 'Enter your current password to save';
                  }
                  return null;
                },
              ),
              const SizedBox(height: 24),
              FilledButton(
                onPressed: _saving ? null : _save,
                child: Text(_saving ? 'Saving…' : 'Save changes'),
              ),
            ],
          ),
        ),
      ),
    );
  }
}
