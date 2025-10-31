import 'package:flutter/material.dart';
import 'models.dart';

class AiChatSettingsPage extends StatefulWidget {
  const AiChatSettingsPage({super.key});

  @override
  State<AiChatSettingsPage> createState() => _AiChatSettingsPageState();
}

class _AiChatSettingsPageState extends State<AiChatSettingsPage> {
  ChatLanguage _preferredLanguage = ChatLanguage.romanUrdu;
  bool _showCulturalTips = true;
  bool _enableHazardAlerts = true;
  bool _enableTransportInfo = true;

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('Chat Settings')),
      body: ListView(
        padding: const EdgeInsets.all(16),
        children: <Widget>[
          Text('Language Preference', style: Theme.of(context).textTheme.titleMedium),
          const SizedBox(height: 8),
          ...ChatLanguage.values.map((ChatLanguage lang) {
            return RadioListTile<ChatLanguage>(
              title: Text(_getLanguageLabel(lang)),
              value: lang,
              groupValue: _preferredLanguage,
              onChanged: (ChatLanguage? v) => setState(() => _preferredLanguage = v ?? ChatLanguage.romanUrdu),
            );
          }),
          const Divider(height: 32),
          SwitchListTile(
            value: _showCulturalTips,
            onChanged: (bool v) => setState(() => _showCulturalTips = v),
            title: const Text('Show Cultural Tips'),
            subtitle: const Text('Include local customs and traditions in responses'),
          ),
          SwitchListTile(
            value: _enableHazardAlerts,
            onChanged: (bool v) => setState(() => _enableHazardAlerts = v),
            title: const Text('Enable Hazard Alerts'),
            subtitle: const Text('Get real-time safety warnings in chat'),
          ),
          SwitchListTile(
            value: _enableTransportInfo,
            onChanged: (bool v) => setState(() => _enableTransportInfo = v),
            title: const Text('Enable Transport Info'),
            subtitle: const Text('Include public transport details in responses'),
          ),
        ],
      ),
    );
  }

  String _getLanguageLabel(ChatLanguage lang) {
    switch (lang) {
      case ChatLanguage.urdu:
        return 'Urdu (اردو)';
      case ChatLanguage.romanUrdu:
        return 'Roman Urdu';
      case ChatLanguage.english:
        return 'English';
    }
  }
}

