enum Region { gilgit, kpk, hazara, murree}

extension RegionLabel on Region {
  String get label {
    switch (this) {
      case Region.gilgit:
        return 'Gilgit-Baltistan';
      case Region.kpk:
        return 'KPK Highlands';
      case Region.hazara:
        return 'Hazara Division';
      case Region.murree:
        return 'Murree & Galyat	';
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

  // ADD THIS METHOD - Convert to backend format
  String get backendValue {
    switch (this) {
      case Activity.hiking:
        return 'hiking';
      case Activity.roadTrip:
        return 'roadtrip';
      case Activity.cityTour:
        return 'city_tour';
      case Activity.camping:
        return 'camping';
      case Activity.photography:
        return 'photography';
      case Activity.cultural:
        return 'cultural';
      case Activity.skiing:
        return 'skiing';
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
  final String area; // NEW: Added area field
  final int month;
  final List<Activity> activities;
  // REMOVED: TravelerProfile profile

  const PackingFormData({
    required this.region,
    required this.area, // NEW
    required this.month,
    required this.activities
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

  // ADD THIS METHOD
  factory PackingItem.fromJson(Map<String, dynamic> json) {
    return PackingItem(
      id: json['id'] ?? '',
      name: json['name'] ?? '',
      notes: json['notes'],
      quantity: json['quantity'] ?? 1,
      checked: json['checked'] ?? false,
    );
  }

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

  // ADD THIS METHOD
  factory PackingSection.fromJson(Map<String, dynamic> json) {
    return PackingSection(
      title: json['title'] ?? '',
      items: (json['items'] as List<dynamic>?)
              ?.map((item) => PackingItem.fromJson(item))
              .toList() ??
          [],
    );
  }
}

String monthName(int m) {
  const List<String> months = <String>[
    'January', 'February', 'March', 'April', 'May', 'June',
    'July', 'August', 'September', 'October', 'November', 'December'
  ];
  return months[m - 1];
}


