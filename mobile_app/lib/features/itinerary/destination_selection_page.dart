import 'package:flutter/material.dart';
import 'models.dart';
import 'api_service.dart';
import '../../routes/app_routes.dart';
import '../../utils/app_constants.dart';

class DestinationSelectionPage extends StatefulWidget {
  final ItineraryFormData form;
  const DestinationSelectionPage({super.key, required this.form});

  @override
  State<DestinationSelectionPage> createState() => _DestinationSelectionPageState();
}

class _DestinationSelectionPageState extends State<DestinationSelectionPage> {
  final ItineraryApiService _apiService = ItineraryApiService();
  List<DestinationRecommendation> _recommendations = [];
  bool _isLoading = true;
  String? _error;

  @override
  void initState() {
    super.initState();
    _loadRecommendations();
  }

  Future<void> _loadRecommendations() async {
    setState(() {
      _isLoading = true;
      _error = null;
    });

    try {
      final mood = _apiService.moodToBackend(widget.form.mood);
      
      final response = await _apiService.recommendDestinations(
        budget: widget.form.budget,
        mood: mood,
        activities: widget.form.activities,
        days: widget.form.durationDays,
        travelMonth: widget.form.travelMonth,
        numRecommendations: 3, // Get 2-3 recommendations as requested
        numPeople: widget.form.numPeople,
      );

      if (response['success'] == true) {
        final recommendationsData = response['recommendations'] as List<dynamic>;
        setState(() {
          _recommendations = recommendationsData
              .map((r) => DestinationRecommendation.fromJson(r as Map<String, dynamic>))
              .toList();
          _isLoading = false;
        });
      } else {
        setState(() {
          _error = response['error'] ?? 'Failed to get recommendations';
          _isLoading = false;
        });
      }
    } catch (e) {
      setState(() {
        _error = e.toString().replaceAll('Exception: ', '');
        _isLoading = false;
      });
    }
  }

  void _selectRecommendation(DestinationRecommendation rec) {
    final updatedForm = ItineraryFormData(
      mood: widget.form.mood,
      budget: widget.form.budget,
      season: widget.form.season,
      activities: widget.form.activities,
      durationDays: widget.form.durationDays,
      destination: rec.destination,
      travelMonth: widget.form.travelMonth,
      startDate: widget.form.startDate,
      numPeople: widget.form.numPeople,
      corridorId: rec.corridorId,
    );

    Navigator.of(context).pushReplacementNamed(
      AppRoutes.itineraryResults,
      arguments: updatedForm,
    );
  }

  @override
  Widget build(BuildContext context) {
    if (_isLoading) {
      return Scaffold(
        appBar: AppBar(title: const Text('Finding Destinations')),
        body: const Center(
          child: Column(
            mainAxisAlignment: MainAxisAlignment.center,
            children: [
              CircularProgressIndicator(),
              SizedBox(height: 16),
              Text('Finding perfect destinations for you...'),
            ],
          ),
        ),
      );
    }

    if (_error != null) {
      return Scaffold(
        appBar: AppBar(title: const Text('Error')),
        body: Center(
          child: Padding(
            padding: const EdgeInsets.all(24.0),
            child: Column(
              mainAxisAlignment: MainAxisAlignment.center,
              children: [
                const Icon(Icons.error_outline, size: 64, color: Colors.red),
                const SizedBox(height: 16),
                Text(
                  'Failed to get recommendations',
                  style: Theme.of(context).textTheme.titleLarge,
                ),
                const SizedBox(height: 8),
                Text(
                  _error!,
                  textAlign: TextAlign.center,
                  style: Theme.of(context).textTheme.bodyMedium,
                ),
                const SizedBox(height: 24),
                FilledButton.icon(
                  onPressed: _loadRecommendations,
                  icon: const Icon(Icons.refresh),
                  label: const Text('Try Again'),
                ),
              ],
            ),
          ),
        ),
      );
    }

    if (_recommendations.isEmpty) {
      return Scaffold(
        appBar: AppBar(title: const Text('No Recommendations')),
        body: const Center(
          child: Text('No destinations found matching your preferences.'),
        ),
      );
    }

    return Scaffold(
      appBar: AppBar(
        title: const Text('Choose Destination'),
      ),
      body: ListView(
        padding: EdgeInsets.all(16).add(AppConstants.footerScrollInsets(context)),
        children: [
          Text(
            'Select a destination to generate your itinerary',
            style: Theme.of(context).textTheme.titleMedium,
          ),
          const SizedBox(height: 8),
          Text(
            'Based on your budget, mood, and preferences',
            style: Theme.of(context).textTheme.bodySmall?.copyWith(
              color: Theme.of(context).colorScheme.onSurfaceVariant,
            ),
          ),
          const SizedBox(height: 24),
          ..._recommendations.map((recommendation) {
            return _RecommendationCard(
              recommendation: recommendation,
              onTap: () => _selectRecommendation(recommendation),
            );
          }),
        ],
      ),
    );
  }
}

class _RecommendationCard extends StatelessWidget {
  final DestinationRecommendation recommendation;
  final VoidCallback onTap;

  const _RecommendationCard({
    required this.recommendation,
    required this.onTap,
  });

  @override
  Widget build(BuildContext context) {
    final preview = recommendation.preview;
    final matchScore = recommendation.matchScore;
    
    return Card(
      margin: const EdgeInsets.only(bottom: 16),
      elevation: 2,
      child: InkWell(
        onTap: onTap,
        borderRadius: BorderRadius.circular(12),
        child: Padding(
          padding: const EdgeInsets.all(16.0),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Row(
                children: [
                  Expanded(
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Text(
                          recommendation.destination,
                          style: Theme.of(context).textTheme.titleLarge,
                        ),
                        const SizedBox(height: 4),
                        Text(
                          recommendation.region,
                          style: Theme.of(context).textTheme.bodyMedium?.copyWith(
                            color: Theme.of(context).colorScheme.onSurfaceVariant,
                          ),
                        ),
                      ],
                    ),
                  ),
                  Container(
                    padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 6),
                    decoration: BoxDecoration(
                      color: Theme.of(context).colorScheme.primaryContainer,
                      borderRadius: BorderRadius.circular(20),
                    ),
                    child: Text(
                      '${matchScore.toStringAsFixed(0)}% match',
                      style: Theme.of(context).textTheme.labelMedium?.copyWith(
                        color: Theme.of(context).colorScheme.onPrimaryContainer,
                        fontWeight: FontWeight.bold,
                      ),
                    ),
                  ),
                ],
              ),
              const SizedBox(height: 12),
              if (preview.highlights.isNotEmpty) ...[
                Text(
                  'Highlights:',
                  style: Theme.of(context).textTheme.labelMedium?.copyWith(
                    fontWeight: FontWeight.bold,
                  ),
                ),
                const SizedBox(height: 4),
                Wrap(
                  spacing: 8,
                  runSpacing: 4,
                  children: preview.highlights.take(3).map((highlight) {
                    return Chip(
                      label: Text(highlight),
                      labelStyle: Theme.of(context).textTheme.labelSmall,
                      padding: EdgeInsets.zero,
                      materialTapTargetSize: MaterialTapTargetSize.shrinkWrap,
                    );
                  }).toList(),
                ),
                const SizedBox(height: 12),
              ],
              Row(
                children: [
                  if (preview.averageRating != null) ...[
                    Icon(Icons.star, size: 16, color: Colors.amber),
                    const SizedBox(width: 4),
                    Text(
                      preview.averageRating!.toStringAsFixed(1),
                      style: Theme.of(context).textTheme.bodySmall,
                    ),
                    const SizedBox(width: 16),
                  ],
                  Icon(Icons.place, size: 16, color: Theme.of(context).colorScheme.onSurfaceVariant),
                  const SizedBox(width: 4),
                  Text(
                    '${preview.poiCount} places',
                    style: Theme.of(context).textTheme.bodySmall,
                  ),
                ],
              ),
              const SizedBox(height: 12),
              if (preview.activities.isNotEmpty) ...[
                Wrap(
                  spacing: 8,
                  runSpacing: 4,
                  children: preview.activities.take(3).map((activity) {
                    return Chip(
                      label: Text(activity),
                      labelStyle: Theme.of(context).textTheme.labelSmall,
                      padding: EdgeInsets.zero,
                      materialTapTargetSize: MaterialTapTargetSize.shrinkWrap,
                    );
                  }).toList(),
                ),
              ],
              const SizedBox(height: 12),
              SizedBox(
                width: double.infinity,
                child: FilledButton.icon(
                  onPressed: onTap,
                  icon: const Icon(Icons.arrow_forward),
                  label: const Text('Select & Generate Itinerary'),
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }
}

