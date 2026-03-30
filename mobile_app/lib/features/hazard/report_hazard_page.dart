import 'package:flutter/material.dart';
import 'models.dart';
import '../../utils/app_constants.dart';
import 'api_service.dart';

class ReportHazardPage extends StatefulWidget {
  const ReportHazardPage({super.key});

  @override
  State<ReportHazardPage> createState() => _ReportHazardPageState();
}

class _ReportHazardPageState extends State<ReportHazardPage> {
  final HazardApiService _apiService = HazardApiService();
  HazardType _type = HazardType.roadblock;
  Severity _severity = Severity.medium;
  final TextEditingController _title = TextEditingController();
  final TextEditingController _desc = TextEditingController();
  final TextEditingController _location = TextEditingController();
  bool _isSubmitting = false;
  bool _isGeocoding = false;

  @override
  void dispose() {
    _title.dispose();
    _desc.dispose();
    _location.dispose();
    super.dispose();
  }

  Future<void> _submitHazard() async {
    if (_title.text.trim().isEmpty || _location.text.trim().isEmpty) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('Please fill all required fields')),
      );
      return;
    }

    setState(() {
      _isSubmitting = true;
      _isGeocoding = true;
    });

    try {
      await _apiService.reportHazard(
        type: _type,
        severity: _severity,
        location: _location.text.trim(),
        title: _title.text.trim(),
        description: _desc.text.trim().isEmpty ? null : _desc.text.trim(),
      );

      if (!mounted) return;

      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(
          content: Text('Hazard reported successfully!'),
          backgroundColor: Colors.green,
        ),
      );

      Navigator.of(context).pop(true); // Return true to indicate success
    } catch (e) {
      if (!mounted) return;

      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(
          content: Text('Error: ${e.toString()}'),
          backgroundColor: Colors.red,
          duration: const Duration(seconds: 4),
        ),
      );
    } finally {
      if (mounted) {
        setState(() {
          _isSubmitting = false;
          _isGeocoding = false;
        });
      }
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('Report Hazard')),
      body: SingleChildScrollView(
        padding: const EdgeInsets.all(16.0).add(AppConstants.footerPadding),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: <Widget>[
            TextField(
              controller: _title,
              decoration: const InputDecoration(
                labelText: 'Title *',
                hintText: 'e.g., Road Block on Karakoram Highway',
                border: OutlineInputBorder(),
              ),
            ),
            const SizedBox(height: 12),
            DropdownButtonFormField<HazardType>(
              value: _type,
              decoration: const InputDecoration(border: OutlineInputBorder(), labelText: 'Hazard Type *'),
              items: HazardType.values
                  .map((HazardType t) => DropdownMenuItem<HazardType>(value: t, child: Text(t.label)))
                  .toList(),
              onChanged: (HazardType? v) => setState(() => _type = v ?? _type),
            ),
            const SizedBox(height: 12),
            DropdownButtonFormField<Severity>(
              value: _severity,
              decoration: const InputDecoration(border: OutlineInputBorder(), labelText: 'Severity *'),
              items: Severity.values
                  .map((Severity s) => DropdownMenuItem<Severity>(value: s, child: Text(s.label)))
                  .toList(),
              onChanged: (Severity? v) => setState(() => _severity = v ?? _severity),
            ),
            const SizedBox(height: 12),
            TextField(
              controller: _location,
              decoration: const InputDecoration(
                labelText: 'Location Name *',
                hintText: 'e.g., Murree, Naran, Gilgit, Karakoram Highway',
                border: OutlineInputBorder(),
                helperText: 'Coordinates will be found automatically',
              ),
            ),
            const SizedBox(height: 12),
            TextField(
              controller: _desc,
              minLines: 3,
              maxLines: 5,
              decoration: const InputDecoration(
                border: OutlineInputBorder(),
                labelText: 'Description (optional)',
                hintText: 'Additional details about the hazard...',
              ),
            ),
            const SizedBox(height: 24),
            if (_isGeocoding)
              const Padding(
                padding: EdgeInsets.only(bottom: 12.0),
                child: Row(
                  children: [
                    SizedBox(
                      width: 20,
                      height: 20,
                      child: CircularProgressIndicator(strokeWidth: 2),
                    ),
                    SizedBox(width: 12),
                    Text('Finding location coordinates...'),
                  ],
                ),
              ),
            SizedBox(
              width: double.infinity,
              child: FilledButton.icon(
                onPressed: _isSubmitting ? null : _submitHazard,
                icon: _isSubmitting
                    ? const SizedBox(
                        width: 20,
                        height: 20,
                        child: CircularProgressIndicator(strokeWidth: 2),
                      )
                    : const Icon(Icons.send_rounded),
                label: Text(_isSubmitting ? 'Submitting...' : 'Submit Report'),
              ),
            )
          ],
        ),
      ),
    );
  }
}


