import 'dart:io' show HttpDate;

class AuthUser {
  final int userId;  final String name;
  final String email;
  final String contactNumber;
  final String dob;
  final String cnic;
  final String medicalConditions;
  final bool isAdmin;
  final bool isActive;

  const AuthUser({
    required this.userId,
    required this.name,
    required this.email,
    required this.contactNumber,
    required this.dob,
    required this.cnic,
    required this.medicalConditions,
    required this.isAdmin,
    required this.isActive,
  });

  /// Normalizes DOB from API/session to `YYYY-MM-DD` for forms and validators.
  static String normalizeDob(String raw) {
    final String t = raw.trim();
    if (t.isEmpty) return t;
    if (RegExp(r'^\d{4}-\d{2}-\d{2}$').hasMatch(t)) return t;
    try {
      final DateTime d = HttpDate.parse(t);
      return '${d.year.toString().padLeft(4, '0')}-'
          '${d.month.toString().padLeft(2, '0')}-'
          '${d.day.toString().padLeft(2, '0')}';
    } catch (_) {
      /* not RFC 1123 */
    }
    final DateTime? iso = DateTime.tryParse(t);
    if (iso != null) {
      final DateTime u = iso.toUtc();
      return '${u.year.toString().padLeft(4, '0')}-'
          '${u.month.toString().padLeft(2, '0')}-'
          '${u.day.toString().padLeft(2, '0')}';
    }
    return t;
  }

  factory AuthUser.fromJson(Map<String, dynamic> json) {
    return AuthUser(
      userId: (json['user_id'] as num?)?.toInt() ?? 0,
      name: json['name'] as String? ?? '',
      email: json['email'] as String? ?? '',
      contactNumber: json['contact_number'] as String? ?? '',
      dob: normalizeDob((json['dob'] ?? '').toString()),
      cnic: json['cnic'] as String? ?? '',
      medicalConditions: json['medical_conditions'] as String? ?? '',
      isAdmin: json['is_admin'] == true,
      isActive: json['is_active'] != false,
    );
  }

  Map<String, dynamic> toJson() {
    return <String, dynamic>{
      'user_id': userId,
      'name': name,
      'email': email,
      'contact_number': contactNumber,
      'dob': dob,
      'cnic': cnic,
      'medical_conditions': medicalConditions,
      'is_admin': isAdmin,
      'is_active': isActive,
    };
  }
}

