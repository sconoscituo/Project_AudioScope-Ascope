import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../core/api/api_client.dart';
import '../../core/providers/subscription_provider.dart';
import '../../core/theme/app_theme.dart';

/// Paywall — 무료 한계 도달 시 showModalBottomSheet으로 띄움.
///
/// 사용법:
/// ```dart
/// showModalBottomSheet(
///   context: context,
///   isScrollControlled: true,
///   backgroundColor: Colors.transparent,
///   builder: (_) => const PaywallScreen(reason: PaywallReason.dailyLimit),
/// );
/// ```
enum PaywallReason {
  dailyLimit,   // 하루 3개 무료 브리핑 소진
  lockedFeature, // 잠긴 기능 접근 시도
}

class PaywallScreen extends ConsumerStatefulWidget {
  final PaywallReason reason;

  const PaywallScreen({
    super.key,
    this.reason = PaywallReason.dailyLimit,
  });

  @override
  ConsumerState<PaywallScreen> createState() => _PaywallScreenState();
}

class _PaywallScreenState extends ConsumerState<PaywallScreen> {
  bool _processing = false;

  String get _headline {
    return switch (widget.reason) {
      PaywallReason.dailyLimit =>
        '오늘의 무료 브리핑을\n모두 들었어요',
      PaywallReason.lockedFeature =>
        'PRO 전용 기능이에요',
    };
  }

  String get _subheadline {
    return switch (widget.reason) {
      PaywallReason.dailyLimit =>
        'PRO로 업그레이드하면 무제한으로\n들을 수 있어요.',
      PaywallReason.lockedFeature =>
        'PRO로 업그레이드하고\n모든 기능을 사용해보세요.',
    };
  }

  @override
  Widget build(BuildContext context) {
    return Container(
      decoration: const BoxDecoration(
        color: AppColors.surfaceCard,
        borderRadius: BorderRadius.vertical(top: Radius.circular(24)),
      ),
      padding: EdgeInsets.fromLTRB(
        24, 16, 24,
        MediaQuery.of(context).viewInsets.bottom + 32,
      ),
      child: Column(
        mainAxisSize: MainAxisSize.min,
        children: [
          // 핸들
          Container(
            width: 40,
            height: 4,
            decoration: BoxDecoration(
              color: AppColors.surfaceLight,
              borderRadius: BorderRadius.circular(2),
            ),
          ),
          const SizedBox(height: 28),

          // 아이콘
          Container(
            width: 64,
            height: 64,
            decoration: BoxDecoration(
              shape: BoxShape.circle,
              color: AppColors.accent.withOpacity(0.1),
              border: Border.all(
                color: AppColors.accent.withOpacity(0.3),
                width: 1.5,
              ),
            ),
            child: const Icon(
              Icons.headphones_rounded,
              size: 30,
              color: AppColors.accent,
            ),
          ),
          const SizedBox(height: 20),

          // 헤드라인
          Text(
            _headline,
            style: const TextStyle(
              fontSize: 22,
              fontWeight: FontWeight.w700,
              color: AppColors.textPrimary,
              height: 1.35,
            ),
            textAlign: TextAlign.center,
          ),
          const SizedBox(height: 8),
          Text(
            _subheadline,
            style: const TextStyle(
              fontSize: 14,
              color: AppColors.textSecondary,
              height: 1.5,
            ),
            textAlign: TextAlign.center,
          ),
          const SizedBox(height: 28),

          // 혜택 3개
          _BenefitRow(
            icon: Icons.all_inclusive_rounded,
            text: '무제한 브리핑',
          ),
          const SizedBox(height: 12),
          _BenefitRow(
            icon: Icons.record_voice_over_rounded,
            text: '고품질 AI 음성',
          ),
          const SizedBox(height: 12),
          _BenefitRow(
            icon: Icons.bookmark_rounded,
            text: '즐겨찾기 무제한',
          ),
          const SizedBox(height: 28),

          // 가격 표시
          Container(
            padding: const EdgeInsets.symmetric(vertical: 12, horizontal: 16),
            decoration: BoxDecoration(
              color: AppColors.surfaceLight,
              borderRadius: BorderRadius.circular(12),
            ),
            child: Row(
              mainAxisAlignment: MainAxisAlignment.center,
              children: [
                const Text(
                  '₩9,900',
                  style: TextStyle(
                    fontSize: 22,
                    fontWeight: FontWeight.w700,
                    color: AppColors.textPrimary,
                  ),
                ),
                const SizedBox(width: 4),
                const Text(
                  '/ 월',
                  style: TextStyle(
                    fontSize: 14,
                    color: AppColors.textSecondary,
                  ),
                ),
                const Spacer(),
                Container(
                  padding:
                      const EdgeInsets.symmetric(horizontal: 8, vertical: 3),
                  decoration: BoxDecoration(
                    color: AppColors.accent.withOpacity(0.15),
                    borderRadius: BorderRadius.circular(20),
                  ),
                  child: const Text(
                    '7일 무료',
                    style: TextStyle(
                      fontSize: 11,
                      fontWeight: FontWeight.w600,
                      color: AppColors.accent,
                    ),
                  ),
                ),
              ],
            ),
          ),
          const SizedBox(height: 16),

          // PRO 시작 버튼
          SizedBox(
            width: double.infinity,
            height: 54,
            child: ElevatedButton(
              onPressed: _processing ? null : _startPro,
              style: ElevatedButton.styleFrom(
                backgroundColor: AppColors.accent,
                foregroundColor: Colors.black,
                shape: RoundedRectangleBorder(
                  borderRadius: BorderRadius.circular(16),
                ),
                elevation: 0,
              ),
              child: _processing
                  ? const SizedBox(
                      width: 20,
                      height: 20,
                      child: CircularProgressIndicator(
                        strokeWidth: 2,
                        color: Colors.black,
                      ),
                    )
                  : const Text(
                      'PRO 시작하기',
                      style: TextStyle(
                        fontSize: 16,
                        fontWeight: FontWeight.w700,
                      ),
                    ),
            ),
          ),
          const SizedBox(height: 12),

          // 나중에 버튼
          TextButton(
            onPressed: () => Navigator.of(context).pop(false),
            child: const Text(
              '나중에',
              style: TextStyle(
                color: AppColors.textTertiary,
                fontSize: 14,
              ),
            ),
          ),
        ],
      ),
    );
  }

  Future<void> _startPro() async {
    setState(() => _processing = true);
    try {
      // TODO: 실제 인앱 결제 연동 후 payment_id 교체
      await ApiClient().post('/api/v1/subscriptions/upgrade', data: {
        'plan': 'monthly',
        'payment_provider': 'google_play',
        'payment_id': 'pending_${DateTime.now().millisecondsSinceEpoch}',
        'price_krw': 9900,
      });
      await ref.read(subscriptionNotifierProvider.notifier).upgradeToPro();
      if (mounted) {
        Navigator.of(context).pop(true); // true = 업그레이드 완료
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(content: Text('PRO가 활성화되었습니다!')),
        );
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
}

class _BenefitRow extends StatelessWidget {
  final IconData icon;
  final String text;

  const _BenefitRow({required this.icon, required this.text});

  @override
  Widget build(BuildContext context) {
    return Row(
      children: [
        Container(
          width: 32,
          height: 32,
          decoration: BoxDecoration(
            color: AppColors.accent.withOpacity(0.12),
            borderRadius: BorderRadius.circular(8),
          ),
          child: Icon(icon, size: 17, color: AppColors.accent),
        ),
        const SizedBox(width: 14),
        Text(
          text,
          style: const TextStyle(
            fontSize: 15,
            fontWeight: FontWeight.w500,
            color: AppColors.textPrimary,
          ),
        ),
        const Spacer(),
        const Icon(Icons.check_rounded, size: 18, color: AppColors.accent),
      ],
    );
  }
}
