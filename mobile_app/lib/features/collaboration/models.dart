class TripGroup {
  final String id;
  final String name;
  final DateTime startDate;
  final DateTime endDate;
  final List<GroupMember> members;
  final String? inviteCode;

  const TripGroup({
    required this.id,
    required this.name,
    required this.startDate,
    required this.endDate,
    required this.members,
    this.inviteCode,
  });
}

class GroupMember {
  final String id;
  final String name;
  final bool isOnline;
  final double? lat;
  final double? lon;
  final DateTime? lastSeen;

  const GroupMember({
    required this.id,
    required this.name,
    this.isOnline = false,
    this.lat,
    this.lon,
    this.lastSeen,
  });
}

class Expense {
  final String id;
  final String description;
  final double amount;
  final String currency;
  final String paidBy;
  final List<String> splitBetween;
  final DateTime timestamp;

  const Expense({
    required this.id,
    required this.description,
    required this.amount,
    required this.currency,
    required this.paidBy,
    required this.splitBetween,
    required this.timestamp,
  });
}

class ExpenseBalance {
  final String person;
  final double balance; // positive = owes, negative = owed

  const ExpenseBalance({required this.person, required this.balance});
}

class Poll {
  final String id;
  final String question;
  final List<String> options;
  final Map<String, String> votes; // userId -> option
  final DateTime? expiresAt;

  const Poll({
    required this.id,
    required this.question,
    required this.options,
    required this.votes,
    this.expiresAt,
  });
}

class DaySummary {
  final int dayNumber;
  final double distanceKm;
  final List<String> placesVisited;
  final List<String> photoUrls;

  const DaySummary({
    required this.dayNumber,
    required this.distanceKm,
    required this.placesVisited,
    required this.photoUrls,
  });
}

class ChatMessage {
  final String id;
  final String senderId;
  final String senderName;
  final String text;
  final DateTime timestamp;
  final String? type; // text, weather, activity, summary, poll

  const ChatMessage({
    required this.id,
    required this.senderId,
    required this.senderName,
    required this.text,
    required this.timestamp,
    this.type,
  });
}

