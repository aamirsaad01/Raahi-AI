class AuthUser {
  final int userId;
  final String name;
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

  factory AuthUser.fromJson(Map<String, dynamic> json) {
    return AuthUser(
      userId: (json['user_id'] as num?)?.toInt() ?? 0,
      name: json['name'] as String? ?? '',
      email: json['email'] as String? ?? '',
      contactNumber: json['contact_number'] as String? ?? '',
      dob: (json['dob'] ?? '').toString(),
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

