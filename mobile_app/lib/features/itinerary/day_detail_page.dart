import 'package:flutter/material.dart';
import 'models.dart';
import '../../routes/app_routes.dart';
import '../../widgets/app_footer_nav.dart';

class DayDetailPage extends StatelessWidget {
  final DayPlan day;
  const DayDetailPage({super.key, required this.day});

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: Text('Day ${day.dayNumber}')),
      body: ListView(
        children: <Widget>[
          ...day.stops.map((Poi p) => ListTile(
                title: Text(p.name),
                subtitle: Text('${p.region} • ${p.activityType} • ${p.difficulty}'),
                trailing: const Icon(Icons.chevron_right),
                onTap: () => Navigator.of(context).pushNamed(AppRoutes.itineraryPoi, arguments: p),
              )),
          if (day.notes != null)
            Padding(
              padding: const EdgeInsets.all(16.0),
              child: Text(day.notes!),
            ),
        ],
      ),
    );
  }
}


