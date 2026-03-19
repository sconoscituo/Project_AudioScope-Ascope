import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:shared_preferences/shared_preferences.dart';

import '../api/api_client.dart';

/// 구독 플랜 상태.
enum SubscriptionPlan { free, pro }

/// 구독 상태 Notifier.
class SubscriptionNotifier extends StateNotifier<SubscriptionPlan> {
  SubscriptionNotifier() : super(SubscriptionPlan.free) {
    _load();
  }

  /// 앱 시작 시 API + 로컬 캐시에서 플랜 로드.
  Future<void> _load() async {
    // 1) 로컬 캐시 먼저 적용 (빠른 UX)
    final prefs = await SharedPreferences.getInstance();
    final cached = prefs.getString('subscription_plan');
    if (cached == 'pro') state = SubscriptionPlan.pro;

    // 2) 서버 최신 정보 반영
    try {
      final response = await ApiClient().get<Map<String, dynamic>>(
        '/api/v1/subscriptions/me',
      );
      final data = ApiClient.extractData<Map<String, dynamic>>(response);
      if (data != null) {
        final plan = data['plan'] as String? ?? 'free';
        final isPro = plan == 'pro' || plan == 'premium' || plan == 'trial';
        state = isPro ? SubscriptionPlan.pro : SubscriptionPlan.free;
        await prefs.setString('subscription_plan', isPro ? 'pro' : 'free');
      }
    } catch (_) {
      // 네트워크 오류 시 캐시 유지
    }
  }

  /// 외부에서 Pro로 전환 (결제 완료 후 호출).
  Future<void> upgradeToPro() async {
    state = SubscriptionPlan.pro;
    final prefs = await SharedPreferences.getInstance();
    await prefs.setString('subscription_plan', 'pro');
  }

  /// 새로고침.
  Future<void> refresh() => _load();
}

/// 구독 상태 Provider.
final subscriptionNotifierProvider =
    StateNotifierProvider<SubscriptionNotifier, SubscriptionPlan>(
  (ref) => SubscriptionNotifier(),
);

/// isPro 편의 getter.
final isProProvider = Provider<bool>((ref) {
  return ref.watch(subscriptionNotifierProvider) == SubscriptionPlan.pro;
});
