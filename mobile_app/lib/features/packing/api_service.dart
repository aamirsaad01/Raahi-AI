import 'dart:convert';
import 'package:http/http.dart' as http;
import 'package:mobile_app/config/api_config.dart';

import 'models.dart';

class PackingApiService {
  /// Generate packing checklist from backend
  Future<PackingChecklistResponse> generateChecklist({
    required String region,
    required String area,
    required int month,
    required List<String> activities,
  }) async {
    try {
      final response = await http.post(
        Uri.parse('${ApiConfig.baseUrl}/api/checklist/generate'),
        headers: {'Content-Type': 'application/json'},
        body: jsonEncode({
          'region': region,
          'area': area,
          'month': month,
          'activities': activities,
        }),
      );

      if (response.statusCode == 200) {
        final data = jsonDecode(response.body);
        return PackingChecklistResponse.fromJson(data);
      } else {
        final error = jsonDecode(response.body);
        throw Exception(error['error'] ?? 'Failed to generate checklist');
      }
    } catch (e) {
      throw Exception('Network error: $e');
    }
  }

  /// Get list of available regions
  Future<List<String>> getRegions() async {
    try {
      final response = await http.get(
        Uri.parse('${ApiConfig.baseUrl}/api/regions'),
      );

      if (response.statusCode == 200) {
        final data = jsonDecode(response.body);
        return List<String>.from(data['regions']);
      } else {
        throw Exception('Failed to fetch regions');
      }
    } catch (e) {
      throw Exception('Network error: $e');
    }
  }

  /// Get list of areas for a specific region
  Future<List<String>> getAreas(String region) async {
    try {
      final response = await http.get(
        Uri.parse('${ApiConfig.baseUrl}/api/areas?region=${Uri.encodeComponent(region)}'),
      );

      if (response.statusCode == 200) {
        final data = jsonDecode(response.body);
        return List<String>.from(data['areas']);
      } else {
        throw Exception('Failed to fetch areas');
      }
    } catch (e) {
      throw Exception('Network error: $e');
    }
  }
}

/// Response model for checklist generation
class PackingChecklistResponse {
  final bool success;
  final List<PackingSection> sections;
  final ChecklistMetadata? metadata;

  const PackingChecklistResponse({
    required this.success,
    required this.sections,
    this.metadata,
  });

  factory PackingChecklistResponse.fromJson(Map<String, dynamic> json) {
    return PackingChecklistResponse(
      success: json['success'] ?? false,
      sections: (json['sections'] as List<dynamic>?)
              ?.map((s) => PackingSection.fromJson(s))
              .toList() ??
          [],
      metadata: json['metadata'] != null
          ? ChecklistMetadata.fromJson(json['metadata'])
          : null,
    );
  }
}

/// Metadata about the generated checklist
class ChecklistMetadata {
  final Map<String, dynamic> destination;
  final Map<String, dynamic> travelInfo;
  final List<String> activities;
  final List<String> warnings;
  final List<String> tips;
  final int totalItems;

  const ChecklistMetadata({
    required this.destination,
    required this.travelInfo,
    required this.activities,
    required this.warnings,
    required this.tips,
    required this.totalItems,
  });

  factory ChecklistMetadata.fromJson(Map<String, dynamic> json) {
    return ChecklistMetadata(
      destination: json['destination'] ?? {},
      travelInfo: json['travel_info'] ?? {},
      activities: List<String>.from(json['activities'] ?? []),
      warnings: List<String>.from(json['warnings'] ?? []),
      tips: List<String>.from(json['tips'] ?? []),
      totalItems: json['total_items'] ?? 0,
    );
  }
}