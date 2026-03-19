import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import '../../core/api/api_client.dart';
import '../../core/auth/auth_service.dart';
import '../../core/providers/providers.dart';
import '../../core/theme/app_theme.dart';

/// 설정 화면. 프로필, 구독, 카테고리, 문의, 로그아웃.
class SettingsScreen extends ConsumerStatefulWidget {
  const SettingsScreen({super.key});

  @override
  ConsumerState<SettingsScreen> createState() => _SettingsScreenState();
}

class _SettingsScreenState extends ConsumerState<SettingsScreen> {
  @override
  Widget build(BuildContext context) {
    final profileAsync = ref.watch(myProfileProvider);
    final subAsync = ref.watch(subscriptionProvider);

    return SafeArea(
      child: ListView(
        padding: const EdgeInsets.all(20),
        children: [
          const Text(
            '설정',
            style: TextStyle(
              fontSize: 24,
              fontWeight: FontWeight.w700,
              color: AppColors.textPrimary,
            ),
          ),
          const SizedBox(height: 24),

          // 프로필 카드
          profileAsync.when(
            data: (profile) => _ProfileCard(profile: profile),
            loading: () => const SizedBox(
              height: 80,
              child: Center(child: CircularProgressIndicator(color: AppColors.accent)),
            ),
            error: (_, __) => const SizedBox(),
          ),
          const SizedBox(height: 20),

          // 구독 상태
          subAsync.when(
            data: (sub) => _SubscriptionCard(sub: sub),
            loading: () => const SizedBox(),
            error: (_, __) => const SizedBox(),
          ),
          const SizedBox(height: 20),

          // 메뉴
          _SettingsTile(
            icon: Icons.tune_rounded,
            title: '뉴스 카테고리',
            subtitle: '관심 분야 설정',
            onTap: () => context.push('/categories/edit'),
          ),
          _SettingsTile(
            icon: Icons.checklist_rounded,
            title: '관심 카테고리 설정',
            subtitle: '카테고리별 체크박스로 세부 설정',
            onTap: () => context.push('/categories/settings'),
          ),
          _SettingsTile(
            icon: Icons.record_voice_over_rounded,
            title: '음성 선택',
            subtitle: '브리핑 나레이터 목소리',
            onTap: () => _showVoiceSelector(context, ref),
          ),
          _SettingsTile(
            icon: Icons.help_outline_rounded,
            title: '자주 묻는 질문',
            subtitle: 'FAQ',
            onTap: () => context.push('/faq'),
          ),
          _SettingsTile(
            icon: Icons.mail_outline_rounded,
            title: '문의하기',
            subtitle: '불편사항이나 건의사항을 알려주세요',
            onTap: () => _showInquiryDialog(context),
          ),
          _SettingsTile(
            icon: Icons.description_outlined,
            title: '이용약관',
            onTap: () => context.push('/terms'),
          ),
          _SettingsTile(
            icon: Icons.privacy_tip_outlined,
            title: '개인정보 처리방침',
            onTap: () => context.push('/privacy'),
          ),
          const SizedBox(height: 12),
          _SettingsTile(
            icon: Icons.logout_rounded,
            title: '로그아웃',
            color: AppColors.error,
            onTap: () async {
              await AuthService.instance.signOut();
              if (context.mounted) context.go('/login');
            },
          ),
          const SizedBox(height: 40),
          const Center(
            child: Text(
              'AudioScope v1.0.0',
              style: TextStyle(fontSize: 12, color: AppColors.textTertiary),
            ),
          ),
        ],
      ),
    );
  }

  void _showVoiceSelector(BuildContext context, WidgetRef ref) {
    showModalBottomSheet(
      context: context,
      backgroundColor: AppColors.surfaceCard,
      shape: const RoundedRectangleBorder(
        borderRadius: BorderRadius.vertical(top: Radius.circular(20)),
      ),
      builder: (ctx) => _VoiceSelectorSheet(ref: ref),
    );
  }

  void _showInquiryDialog(BuildContext context) {
    final subjectCtrl = TextEditingController();
    final messageCtrl = TextEditingController();

    showModalBottomSheet(
      context: context,
      isScrollControlled: true,
      backgroundColor: AppColors.surfaceCard,
      shape: const RoundedRectangleBorder(
        borderRadius: BorderRadius.vertical(top: Radius.circular(20)),
      ),
      builder: (ctx) {
        return Padding(
          padding: EdgeInsets.fromLTRB(
            20, 20, 20,
            MediaQuery.of(ctx).viewInsets.bottom + 20,
          ),
          child: Column(
            mainAxisSize: MainAxisSize.min,
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              const Text(
                '문의하기',
                style: TextStyle(fontSize: 20, fontWeight: FontWeight.w700, color: AppColors.textPrimary),
              ),
              const SizedBox(height: 16),
              TextField(
                controller: subjectCtrl,
                style: const TextStyle(color: AppColors.textPrimary),
                decoration: InputDecoration(
                  hintText: '제목',
                  hintStyle: const TextStyle(color: AppColors.textTertiary),
                  filled: true,
                  fillColor: AppColors.surfaceLight,
                  border: OutlineInputBorder(
                    borderRadius: BorderRadius.circular(12),
                    borderSide: BorderSide.none,
                  ),
                ),
              ),
              const SizedBox(height: 12),
              TextField(
                controller: messageCtrl,
                style: const TextStyle(color: AppColors.textPrimary),
                maxLines: 4,
                decoration: InputDecoration(
                  hintText: '내용을 입력해주세요',
                  hintStyle: const TextStyle(color: AppColors.textTertiary),
                  filled: true,
                  fillColor: AppColors.surfaceLight,
                  border: OutlineInputBorder(
                    borderRadius: BorderRadius.circular(12),
                    borderSide: BorderSide.none,
                  ),
                ),
              ),
              const SizedBox(height: 16),
              SizedBox(
                width: double.infinity,
                height: 50,
                child: ElevatedButton(
                  onPressed: () async {
                    try {
                      await ApiClient().post('/api/v1/users/me/inquiry', data: {
                        'subject': subjectCtrl.text,
                        'message': messageCtrl.text,
                      });
                      if (ctx.mounted) {
                        Navigator.pop(ctx);
                        ScaffoldMessenger.of(context).showSnackBar(
                          const SnackBar(content: Text('문의가 접수되었습니다')),
                        );
                      }
                    } catch (_) {}
                  },
                  child: const Text('보내기'),
                ),
              ),
            ],
          ),
        );
      },
    );
  }
}

class _VoiceSelectorSheet extends StatefulWidget {
  final WidgetRef ref;
  const _VoiceSelectorSheet({required this.ref});

  @override
  State<_VoiceSelectorSheet> createState() => _VoiceSelectorSheetState();
}

class _VoiceSelectorSheetState extends State<_VoiceSelectorSheet> {
  List<Map<String, dynamic>> _voices = [];
  bool _loading = true;
  String? _selectedVoiceId;

  @override
  void initState() {
    super.initState();
    _loadData();
  }

  Future<void> _loadData() async {
    try {
      // 현재 선택된 음성 가져오기
      final profile = widget.ref.read(myProfileProvider).valueOrNull;
      _selectedVoiceId = profile?['preferred_voice_id'] as String? ?? 'ko-KR-female-1';

      // 음성 목록 가져오기
      final response = await ApiClient().get<Map<String, dynamic>>('/api/v1/users/voices');
      final data = ApiClient.extractData<List<dynamic>>(response);
      if (mounted) {
        setState(() {
          _voices = data?.cast<Map<String, dynamic>>() ?? [];
          _loading = false;
        });
      }
    } catch (_) {
      if (mounted) setState(() => _loading = false);
    }
  }

  Future<void> _selectVoice(String voiceId) async {
    try {
      await ApiClient().patch('/api/v1/users/me/voice', data: {'voice_id': voiceId});
      widget.ref.invalidate(myProfileProvider);
      if (mounted) {
        setState(() => _selectedVoiceId = voiceId);
        Navigator.pop(context);
      }
    } catch (_) {}
  }

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.fromLTRB(20, 20, 20, 32),
      child: Column(
        mainAxisSize: MainAxisSize.min,
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          const Text(
            '음성 선택',
            style: TextStyle(
              fontSize: 20,
              fontWeight: FontWeight.w700,
              color: AppColors.textPrimary,
            ),
          ),
          const SizedBox(height: 16),
          if (_loading)
            const Center(
              child: Padding(
                padding: EdgeInsets.symmetric(vertical: 24),
                child: CircularProgressIndicator(color: AppColors.accent),
              ),
            )
          else
            ..._voices.map((voice) {
              final id = voice['id'] as String;
              final name = voice['name'] as String;
              final isSelected = id == _selectedVoiceId;
              return ListTile(
                contentPadding: EdgeInsets.zero,
                title: Text(
                  name,
                  style: TextStyle(
                    fontSize: 15,
                    color: isSelected ? AppColors.accent : AppColors.textPrimary,
                    fontWeight: isSelected ? FontWeight.w600 : FontWeight.normal,
                  ),
                ),
                trailing: isSelected
                    ? const Icon(Icons.check_rounded, color: AppColors.accent)
                    : null,
                onTap: () => _selectVoice(id),
              );
            }),
        ],
      ),
    );
  }
}

class _ProfileCard extends StatelessWidget {
  final Map<String, dynamic> profile;
  const _ProfileCard({required this.profile});

  @override
  Widget build(BuildContext context) {
    final name = profile['display_name'] as String? ?? '사용자';
    final email = profile['email'] as String? ?? '';
    final imageUrl = profile['profile_image_url'] as String?;
    final listenCount = profile['total_listen_count'] as int? ?? 0;

    return Container(
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        color: AppColors.surfaceCard,
        borderRadius: BorderRadius.circular(16),
      ),
      child: Row(
        children: [
          CircleAvatar(
            radius: 28,
            backgroundColor: AppColors.surfaceLight,
            backgroundImage: imageUrl != null ? NetworkImage(imageUrl) : null,
            child: imageUrl == null
                ? const Icon(Icons.person_rounded, color: AppColors.textTertiary, size: 28)
                : null,
          ),
          const SizedBox(width: 14),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(name,
                    style: const TextStyle(fontSize: 17, fontWeight: FontWeight.w600, color: AppColors.textPrimary)),
                Text(email, style: const TextStyle(fontSize: 13, color: AppColors.textTertiary)),
              ],
            ),
          ),
          Column(
            children: [
              Text('$listenCount',
                  style: const TextStyle(fontSize: 20, fontWeight: FontWeight.w700, color: AppColors.accent)),
              const Text('청취', style: TextStyle(fontSize: 11, color: AppColors.textTertiary)),
            ],
          ),
        ],
      ),
    );
  }
}

class _SubscriptionCard extends StatelessWidget {
  final Map<String, dynamic> sub;
  const _SubscriptionCard({required this.sub});

  @override
  Widget build(BuildContext context) {
    final isPremium = sub['is_active_premium'] == true;

    return GestureDetector(
      onTap: () => context.push('/subscription'),
      child: Container(
        padding: const EdgeInsets.all(16),
        decoration: BoxDecoration(
          gradient: isPremium
              ? const LinearGradient(colors: [AppColors.premiumGradientStart, AppColors.surfaceCard])
              : null,
          color: isPremium ? null : AppColors.surfaceCard,
          borderRadius: BorderRadius.circular(16),
          border: isPremium ? Border.all(color: AppColors.premiumGold.withOpacity(0.3)) : null,
        ),
        child: Row(
          children: [
            Icon(
              isPremium ? Icons.workspace_premium_rounded : Icons.star_outline_rounded,
              color: isPremium ? AppColors.premiumGold : AppColors.textTertiary,
              size: 28,
            ),
            const SizedBox(width: 12),
            Expanded(
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(
                    isPremium ? 'Premium' : 'Free Plan',
                    style: TextStyle(
                      fontSize: 16,
                      fontWeight: FontWeight.w600,
                      color: isPremium ? AppColors.premiumGold : AppColors.textPrimary,
                    ),
                  ),
                  Text(
                    isPremium ? '모든 브리핑 무제한' : '아침 브리핑 1회/일 · 광고 시청 시 +1회',
                    style: const TextStyle(fontSize: 12, color: AppColors.textTertiary),
                  ),
                ],
              ),
            ),
            if (!isPremium)
              Container(
                padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 6),
                decoration: BoxDecoration(
                  color: AppColors.accent,
                  borderRadius: BorderRadius.circular(20),
                ),
                child: const Text('업그레이드',
                    style: TextStyle(fontSize: 12, fontWeight: FontWeight.w600, color: Colors.white)),
              ),
          ],
        ),
      ),
    );
  }
}

class _SettingsTile extends StatelessWidget {
  final IconData icon;
  final String title;
  final String? subtitle;
  final Color? color;
  final VoidCallback onTap;

  const _SettingsTile({
    required this.icon,
    required this.title,
    this.subtitle,
    this.color,
    required this.onTap,
  });

  @override
  Widget build(BuildContext context) {
    return ListTile(
      contentPadding: const EdgeInsets.symmetric(horizontal: 4, vertical: 2),
      leading: Icon(icon, color: color ?? AppColors.textSecondary, size: 22),
      title: Text(title, style: TextStyle(fontSize: 15, color: color ?? AppColors.textPrimary)),
      subtitle: subtitle != null
          ? Text(subtitle!, style: const TextStyle(fontSize: 12, color: AppColors.textTertiary))
          : null,
      trailing: const Icon(Icons.chevron_right_rounded, color: AppColors.textTertiary),
      onTap: onTap,
    );
  }
}
