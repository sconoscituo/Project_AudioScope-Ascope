import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import '../../core/api/api_client.dart';
import '../../core/constants/app_constants.dart';
import '../../core/providers/providers.dart';
import '../../core/theme/app_theme.dart';

/// 구독/프리미엄 화면.
class SubscriptionScreen extends ConsumerStatefulWidget {
  const SubscriptionScreen({super.key});

  @override
  ConsumerState<SubscriptionScreen> createState() => _SubscriptionScreenState();
}

class _SubscriptionScreenState extends ConsumerState<SubscriptionScreen> {
  String _selectedPlan = 'monthly';
  bool _processing = false;

  @override
  Widget build(BuildContext context) {
    final subAsync = ref.watch(subscriptionProvider);

    return Scaffold(
      backgroundColor: AppColors.primary,
      appBar: AppBar(
        title: const Text('Premium'),
        leading: IconButton(
          icon: const Icon(Icons.arrow_back_ios_new_rounded, size: 20),
          onPressed: () => context.pop(),
        ),
      ),
      body: SingleChildScrollView(
        padding: const EdgeInsets.all(20),
        child: Column(
          children: [
            // 프리미엄 헤더
            Container(
              width: double.infinity,
              padding: const EdgeInsets.all(28),
              decoration: BoxDecoration(
                gradient: const LinearGradient(
                  begin: Alignment.topLeft,
                  end: Alignment.bottomRight,
                  colors: [Color(0xFF1E3A5F), Color(0xFF0D1B2A)],
                ),
                borderRadius: BorderRadius.circular(24),
                border: Border.all(color: AppColors.premiumGold.withOpacity(0.3)),
              ),
              child: Column(
                children: [
                  Icon(Icons.workspace_premium_rounded,
                      size: 56, color: AppColors.premiumGold),
                  const SizedBox(height: 16),
                  const Text(
                    'AudioScope Premium',
                    style: TextStyle(
                      fontSize: 24,
                      fontWeight: FontWeight.w700,
                      color: AppColors.premiumGold,
                    ),
                  ),
                  const SizedBox(height: 8),
                  const Text(
                    '하루 3회 브리핑을 무제한으로',
                    style: TextStyle(fontSize: 15, color: AppColors.textSecondary),
                  ),
                ],
              ),
            ),
            const SizedBox(height: 28),

            // 혜택 리스트
            _BenefitItem(icon: Icons.headphones, text: '아침/점심/저녁 모든 브리핑 무제한'),
            _BenefitItem(icon: Icons.article_outlined, text: '기사 원문 + AI 요약 무제한'),
            _BenefitItem(icon: Icons.tune, text: '맞춤 카테고리 우선 반영'),
            _BenefitItem(icon: Icons.history, text: '전체 히스토리 열람'),
            _BenefitItem(icon: Icons.block, text: '광고 없는 쾌적한 경험'),
            const SizedBox(height: 28),

            // 플랜 선택
            Row(
              children: [
                Expanded(
                  child: _PlanCard(
                    title: '월간',
                    price: '${AppConstants.premiumMonthlyKRW}원/월',
                    isSelected: _selectedPlan == 'monthly',
                    onTap: () => setState(() => _selectedPlan = 'monthly'),
                  ),
                ),
                const SizedBox(width: 12),
                Expanded(
                  child: _PlanCard(
                    title: '연간',
                    price: '${AppConstants.premiumYearlyKRW}원/년',
                    badge: '33% 할인',
                    isSelected: _selectedPlan == 'yearly',
                    onTap: () => setState(() => _selectedPlan = 'yearly'),
                  ),
                ),
              ],
            ),
            const SizedBox(height: 24),

            // 구독 버튼
            SizedBox(
              width: double.infinity,
              height: 56,
              child: ElevatedButton(
                onPressed: _processing ? null : _subscribe,
                style: ElevatedButton.styleFrom(
                  backgroundColor: AppColors.premiumGold,
                  shape: RoundedRectangleBorder(
                    borderRadius: BorderRadius.circular(16),
                  ),
                ),
                child: _processing
                    ? const SizedBox(
                        width: 20, height: 20,
                        child: CircularProgressIndicator(strokeWidth: 2, color: Colors.white),
                      )
                    : const Text(
                        '프리미엄 시작하기',
                        style: TextStyle(
                          fontSize: 17,
                          fontWeight: FontWeight.w700,
                          color: Colors.white,
                        ),
                      ),
              ),
            ),
            const SizedBox(height: 12),

            // 무료 체험
            TextButton(
              onPressed: _startTrial,
              child: const Text(
                '${AppConstants.trialDays}일 무료 체험 시작',
                style: TextStyle(color: AppColors.accent, fontSize: 14),
              ),
            ),

            const SizedBox(height: 20),
            const Text(
              '구독은 언제든 취소할 수 있습니다.\n결제 관련 문의: 설정 > 문의하기',
              style: TextStyle(fontSize: 12, color: AppColors.textTertiary, height: 1.5),
              textAlign: TextAlign.center,
            ),
          ],
        ),
      ),
    );
  }

  Future<void> _subscribe() async {
    setState(() => _processing = true);
    try {
      // TODO: 실제 인앱 결제 연동 (Google Play / App Store)
      await ApiClient().post('/api/v1/subscriptions/upgrade', data: {
        'plan': _selectedPlan,
        'payment_provider': 'google_play',
        'payment_id': 'pending_${DateTime.now().millisecondsSinceEpoch}',
        'price_krw': _selectedPlan == 'monthly'
            ? AppConstants.premiumMonthlyKRW
            : AppConstants.premiumYearlyKRW,
      });
      ref.invalidate(subscriptionProvider);
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(content: Text('프리미엄이 활성화되었습니다!')),
        );
        context.pop();
      }
    } catch (_) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(content: Text('결제 처리 중 오류가 발생했습니다')),
        );
      }
    } finally {
      if (mounted) setState(() => _processing = false);
    }
  }

  Future<void> _startTrial() async {
    try {
      await ApiClient().post('/api/v1/subscriptions/upgrade', data: {
        'plan': 'trial',
        'payment_provider': 'trial',
        'payment_id': 'trial_${DateTime.now().millisecondsSinceEpoch}',
        'price_krw': 0,
      });
      ref.invalidate(subscriptionProvider);
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(content: Text('무료 체험이 시작되었습니다!')),
        );
        context.pop();
      }
    } catch (_) {}
  }
}

class _BenefitItem extends StatelessWidget {
  final IconData icon;
  final String text;
  const _BenefitItem({required this.icon, required this.text});

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.only(bottom: 14),
      child: Row(
        children: [
          Icon(icon, size: 20, color: AppColors.premiumGold),
          const SizedBox(width: 12),
          Expanded(
            child: Text(text, style: const TextStyle(fontSize: 15, color: AppColors.textPrimary)),
          ),
        ],
      ),
    );
  }
}

class _PlanCard extends StatelessWidget {
  final String title;
  final String price;
  final String? badge;
  final bool isSelected;
  final VoidCallback onTap;

  const _PlanCard({
    required this.title,
    required this.price,
    this.badge,
    required this.isSelected,
    required this.onTap,
  });

  @override
  Widget build(BuildContext context) {
    return GestureDetector(
      onTap: onTap,
      child: AnimatedContainer(
        duration: const Duration(milliseconds: 200),
        padding: const EdgeInsets.all(16),
        decoration: BoxDecoration(
          color: isSelected ? AppColors.accent.withOpacity(0.1) : AppColors.surfaceCard,
          borderRadius: BorderRadius.circular(16),
          border: Border.all(
            color: isSelected ? AppColors.accent : AppColors.surfaceLight,
            width: isSelected ? 2 : 1,
          ),
        ),
        child: Column(
          children: [
            if (badge != null)
              Container(
                margin: const EdgeInsets.only(bottom: 8),
                padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 2),
                decoration: BoxDecoration(
                  color: AppColors.success.withOpacity(0.2),
                  borderRadius: BorderRadius.circular(10),
                ),
                child: Text(badge!, style: const TextStyle(fontSize: 10, color: AppColors.success, fontWeight: FontWeight.w600)),
              ),
            Text(title, style: TextStyle(
              fontSize: 16, fontWeight: FontWeight.w600,
              color: isSelected ? AppColors.accent : AppColors.textPrimary,
            )),
            const SizedBox(height: 4),
            Text(price, style: const TextStyle(fontSize: 13, color: AppColors.textSecondary)),
          ],
        ),
      ),
    );
  }
}
