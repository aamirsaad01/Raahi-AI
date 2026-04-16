import 'package:flutter/material.dart';

import 'auth_service.dart';

class SignupPage extends StatefulWidget {
  const SignupPage({super.key});

  @override
  State<SignupPage> createState() => _SignupPageState();
}

class _SignupPageState extends State<SignupPage> {
  final _formKey = GlobalKey<FormState>();
  final _nameCtrl = TextEditingController();
  final _emailCtrl = TextEditingController();
  final _contactCtrl = TextEditingController();
  final _dobCtrl = TextEditingController();
  final _cnicCtrl = TextEditingController();
  final _medicalCtrl = TextEditingController();
  final _pwdCtrl = TextEditingController();
  bool _loading = false;

  @override
  void dispose() {
    _nameCtrl.dispose();
    _emailCtrl.dispose();
    _contactCtrl.dispose();
    _dobCtrl.dispose();
    _cnicCtrl.dispose();
    _medicalCtrl.dispose();
    _pwdCtrl.dispose();
    super.dispose();
  }

  Future<void> _submit() async {
    if (!_formKey.currentState!.validate()) return;
    setState(() => _loading = true);
    try {
      await AuthService().register(
        name: _nameCtrl.text,
        email: _emailCtrl.text,
        contactNumber: _contactCtrl.text,
        dob: _dobCtrl.text,
        cnic: _cnicCtrl.text,
        medicalConditions: _medicalCtrl.text,
        password: _pwdCtrl.text,
      );
      if (!mounted) return;
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('Signup successful. Please login.')),
      );
      Navigator.of(context).pop();
    } catch (e) {
      if (!mounted) return;
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text(e.toString().replaceFirst('Exception: ', ''))),
      );
    } finally {
      if (mounted) setState(() => _loading = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('Signup')),
      body: SingleChildScrollView(
        padding: const EdgeInsets.all(16),
        child: Form(
          key: _formKey,
          child: Column(
            children: <Widget>[
              TextFormField(
                controller: _nameCtrl,
                decoration: const InputDecoration(labelText: 'Name'),
                validator: (v) => (v == null || v.trim().length < 2)
                    ? 'Name required'
                    : null,
              ),
              const SizedBox(height: 10),
              TextFormField(
                controller: _emailCtrl,
                decoration: const InputDecoration(labelText: 'Email'),
                validator: (v) => (v == null || !v.contains('@'))
                    ? 'Valid email required'
                    : null,
              ),
              const SizedBox(height: 10),
              TextFormField(
                controller: _contactCtrl,
                decoration: const InputDecoration(labelText: 'Contact Number'),
                validator: (v) => (v == null || v.trim().length < 10)
                    ? 'Contact required'
                    : null,
              ),
              const SizedBox(height: 10),
              TextFormField(
                controller: _dobCtrl,
                decoration: const InputDecoration(
                  labelText: 'DOB (YYYY-MM-DD)',
                ),
                validator: (v) => (v == null || v.trim().isEmpty)
                    ? 'DOB required'
                    : null,
              ),
              const SizedBox(height: 10),
              TextFormField(
                controller: _cnicCtrl,
                decoration: const InputDecoration(labelText: 'CNIC'),
                validator: (v) => (v == null || v.trim().isEmpty)
                    ? 'CNIC required'
                    : null,
              ),
              const SizedBox(height: 10),
              TextFormField(
                controller: _medicalCtrl,
                decoration: const InputDecoration(
                  labelText: 'Medical Conditions (optional)',
                ),
              ),
              const SizedBox(height: 10),
              TextFormField(
                controller: _pwdCtrl,
                obscureText: true,
                decoration: const InputDecoration(labelText: 'Password'),
                validator: (v) => (v == null || v.length < 8)
                    ? 'At least 8 chars'
                    : null,
              ),
              const SizedBox(height: 20),
              FilledButton(
                onPressed: _loading ? null : _submit,
                child: Text(_loading ? 'Creating account...' : 'Signup'),
              ),
            ],
          ),
        ),
      ),
    );
  }
}

