import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../api/api_client.dart';

/// 오늘의 브리핑 목록 Provider.
final todayBriefingsProvider =
    FutureProvider.autoDispose<List<Map<String, dynamic>>>((ref) async {
  final response = await ApiClient().get<Map<String, dynamic>>(
    '/api/v1/briefings/today',
  );
  final data = ApiClient.extractData<List<dynamic>>(response);
  return data?.cast<Map<String, dynamic>>() ?? [];
});

/// 브리핑 히스토리 Provider (페이지네이션).
final briefingHistoryProvider = FutureProvider.autoDispose
    .family<Map<String, dynamic>, int>((ref, page) async {
  final response = await ApiClient().get<Map<String, dynamic>>(
    '/api/v1/briefings/history',
    queryParameters: {'page': page, 'size': 20},
  );
  return ApiClient.extractData<Map<String, dynamic>>(response) ?? {};
});

/// 주간 트렌드 Provider.
final weeklyTrendsProvider = FutureProvider.autoDispose
    .family<Map<String, dynamic>, int>((ref, weekOffset) async {
  final response = await ApiClient().get<Map<String, dynamic>>(
    '/api/v1/trends/weekly',
    queryParameters: {'week_offset': weekOffset},
  );
  return ApiClient.extractData<Map<String, dynamic>>(response) ?? {};
});

/// 구독 정보 Provider.
final subscriptionProvider =
    FutureProvider.autoDispose<Map<String, dynamic>>((ref) async {
  final response = await ApiClient().get<Map<String, dynamic>>(
    '/api/v1/subscriptions/me',
  );
  return ApiClient.extractData<Map<String, dynamic>>(response) ?? {};
});

/// 내 정보 Provider.
final myProfileProvider =
    FutureProvider.autoDispose<Map<String, dynamic>>((ref) async {
  final response = await ApiClient().get<Map<String, dynamic>>(
    '/api/v1/users/me',
  );
  return ApiClient.extractData<Map<String, dynamic>>(response) ?? {};
});

/// 카테고리 Provider.
final categoriesProvider =
    FutureProvider.autoDispose<Map<String, dynamic>>((ref) async {
  final response = await ApiClient().get<Map<String, dynamic>>(
    '/api/v1/users/me/categories',
  );
  return ApiClient.extractData<Map<String, dynamic>>(response) ?? {};
});

/// 안 들은 브리핑 Provider.
final unlistenedProvider =
    FutureProvider.autoDispose<List<Map<String, dynamic>>>((ref) async {
  final response = await ApiClient().get<Map<String, dynamic>>(
    '/api/v1/briefings/unlistened',
  );
  final data = ApiClient.extractData<List<dynamic>>(response);
  return data?.cast<Map<String, dynamic>>() ?? [];
});
