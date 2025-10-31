import 'package:flutter/material.dart';
import 'models.dart';

class ReportHazardPage extends StatefulWidget {
  const ReportHazardPage({super.key});

  @override
  State<ReportHazardPage> createState() => _ReportHazardPageState();
}

class _ReportHazardPageState extends State<ReportHazardPage> {
  HazardType _type = HazardType.roadblock;
  Severity _severity = Severity.medium;
  final TextEditingController _desc = TextEditingController();
  final TextEditingController _location = TextEditingController();
  final TextEditingController _lat = TextEditingController();
  final TextEditingController _lon = TextEditingController();

  @override
  void dispose() {
    _desc.dispose();
    _location.dispose();
    _lat.dispose();
    _lon.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('Report Hazard')),
      body: Padding(
        padding: const EdgeInsets.all(16.0),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: <Widget>[
            DropdownButtonFormField<HazardType>(
              value: _type,
              decoration: const InputDecoration(border: OutlineInputBorder(), labelText: 'Type'),
              items: HazardType.values
                  .map((HazardType t) => DropdownMenuItem<HazardType>(value: t, child: Text(t.label)))
                  .toList(),
              onChanged: (HazardType? v) => setState(() => _type = v ?? _type),
            ),
            const SizedBox(height: 12),
            DropdownButtonFormField<Severity>(
              value: _severity,
              decoration: const InputDecoration(border: OutlineInputBorder(), labelText: 'Severity'),
              items: Severity.values
                  .map((Severity s) => DropdownMenuItem<Severity>(value: s, child: Text(s.label)))
                  .toList(),
              onChanged: (Severity? v) => setState(() => _severity = v ?? _severity),
            ),
            const SizedBox(height: 12),
            TextField(
              controller: _location,
              decoration: const InputDecoration(labelText: 'Location', border: OutlineInputBorder()),
            ),
            const SizedBox(height: 12),
            Row(
              children: <Widget>[
                Expanded(
                  child: TextField(
                    controller: _lat,
                    keyboardType: const TextInputType.numberWithOptions(decimal: true, signed: true),
                    decoration: const InputDecoration(labelText: 'Latitude', border: OutlineInputBorder()),
                  ),
                ),
                const SizedBox(width: 8),
                Expanded(
                  child: TextField(
                    controller: _lon,
                    keyboardType: const TextInputType.numberWithOptions(decimal: true, signed: true),
                    decoration: const InputDecoration(labelText: 'Longitude', border: OutlineInputBorder()),
                  ),
                ),
              ],
            ),
            const SizedBox(height: 12),
            TextField(
              controller: _desc,
              minLines: 3,
              maxLines: 5,
              decoration: const InputDecoration(border: OutlineInputBorder(), labelText: 'Description (optional)'),
            ),
            const Spacer(),
            SizedBox(
              width: double.infinity,
              child: FilledButton.icon(
                onPressed: () {
                  if (_location.text.trim().isEmpty || _lat.text.trim().isEmpty || _lon.text.trim().isEmpty) {
                    ScaffoldMessenger.of(context).showSnackBar(const SnackBar(content: Text('Fill all required fields')));
                    return;
                  }
                  final double? lat = double.tryParse(_lat.text.trim());
                  final double? lon = double.tryParse(_lon.text.trim());
                  if (lat == null || lon == null) {
                    ScaffoldMessenger.of(context).showSnackBar(const SnackBar(content: Text('Enter valid coordinates')));
                    return;
                  }
                  ScaffoldMessenger.of(context).showSnackBar(const SnackBar(content: Text('Hazard reported (stub).')));
                  Navigator.of(context).pop();
                },
                icon: const Icon(Icons.send_rounded),
                label: const Text('Submit'),
              ),
            )
          ],
        ),
      ),
    );
  }
}


