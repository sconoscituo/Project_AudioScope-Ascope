import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../core/api/api_client.dart';

/// 즐겨찾기 목록 Provider.
final favoritesProvider =
    FutureProvider.autoDispose<List<Map<String, dynamic>>>((ref) async {
  final response = await ApiClient().get<Map<String, dynamic>>(
    '/api/v1/favorites',
  );
  final data = ApiClient.extractData<List<dynamic>>(response);
  return data?.cast<Map<String, dynamic>>() ?? [];
});

/// 즐겨찾기 삭제 Notifier.
/// removeFavorite() 호출 후 favoritesProvider를 자동으로 갱신한다.
class FavoritesNotifier extends StateNotifier<AsyncValue<void>> {
  final Ref _ref;

  FavoritesNotifier(this._ref) : super(const AsyncValue.data(null));

  Future<void> removeFavorite(String id) async {
    state = const AsyncValue.loading();
    try {
      await ApiClient().deleteFavorite(id);
      state = const AsyncValue.data(null);
      _ref.invalidate(favoritesProvider);
    } catch (e, st) {
      state = AsyncValue.error(e, st);
    }
  }
}

final favoritesNotifierProvider =
    StateNotifierProvider.autoDispose<FavoritesNotifier, AsyncValue<void>>(
  (ref) => FavoritesNotifier(ref),
);
