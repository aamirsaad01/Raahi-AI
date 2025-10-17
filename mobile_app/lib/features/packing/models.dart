enum Region { north, central, south, coastal, desert, highlands }

extension RegionLabel on Region {
  String get label {
    switch (this) {
      case Region.north:
        return 'North';
      case Region.central:
        return 'Central';
      case Region.south:
        return 'South';
      case Region.coastal:
        return 'Coastal';
      case Region.desert:
        return 'Desert';
      case Region.highlands:
        return 'Highlands';
    }
  }
}

enum Activity { hiking, roadTrip, cityTour, camping, photography, cultural, skiing }

extension ActivityLabel on Activity {
  String get label {
    switch (this) {
      case Activity.hiking:
        return 'Hiking';
      case Activity.roadTrip:
        return 'Road Trip';
      case Activity.cityTour:
        return 'City Tour';
      case Activity.camping:
        return 'Camping';
      case Activity.photography:
        return 'Photography';
      case Activity.cultural:
        return 'Cultural';
      case Activity.skiing:
        return 'Skiing';
    }
  }
}

enum TravelerProfile { standard, withKids, elderly, medicalNeeds }

extension TravelerProfileLabel on TravelerProfile {
  String get label {
    switch (this) {
      case TravelerProfile.standard:
        return 'Standard';
      case TravelerProfile.withKids:
        return 'With Kids';
      case TravelerProfile.elderly:
        return 'Elderly';
      case TravelerProfile.medicalNeeds:
        return 'Medical Needs';
    }
  }
}

class PackingFormData {
  final Region region;
  final int month;
  final List<Activity> activities;
  final TravelerProfile profile;

  const PackingFormData({
    required this.region,
    required this.month,
    required this.activities,
    required this.profile,
  });
}

class PackingItem {
  final String id;
  final String name;
  final String? notes;
  final int quantity;
  final bool checked;

  const PackingItem({
    required this.id,
    required this.name,
    this.notes,
    this.quantity = 1,
    this.checked = false,
  });

  PackingItem copyWith({
    String? id,
    String? name,
    String? notes,
    int? quantity,
    bool? checked,
  }) {
    return PackingItem(
      id: id ?? this.id,
      name: name ?? this.name,
      notes: notes ?? this.notes,
      quantity: quantity ?? this.quantity,
      checked: checked ?? this.checked,
    );
  }
}

class PackingSection {
  final String title;
  final List<PackingItem> items;

  const PackingSection({required this.title, required this.items});
}

String monthName(int m) {
  const List<String> months = <String>[
    'January', 'February', 'March', 'April', 'May', 'June',
    'July', 'August', 'September', 'October', 'November', 'December'
  ];
  return months[m - 1];
}


