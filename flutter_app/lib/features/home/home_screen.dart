import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import 'package:intl/intl.dart';

import '../../core/constants/app_constants.dart';
import '../../core/providers/providers.dart';
import '../../core/theme/app_theme.dart';
import '../briefing/audio_player_widget.dart';

/// 홈 화면. 오늘의 브리핑 카드 + 하단 네비게이션.
class HomeScreen extends ConsumerStatefulWidget {
  final Widget child;
  const HomeScreen({super.key, required this.child});

  @override
  ConsumerState<HomeScreen> createState() => _HomeScreenState();
}

class _HomeScreenState extends ConsumerState<HomeScreen> {
  int _currentIndex = 0;

  final _tabs = ['/home', '/trends', '/settings'];

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: AppColors.primary,
      body: widget.child,
      bottomNavigationBar: Container(
        decoration: BoxDecoration(
          color: AppColors.surface,
          border: Border(
            top: BorderSide(color: AppColors.surfaceLight, width: 0.5),
          ),
        ),
        child: BottomNavigationBar(
          currentIndex: _currentIndex,
          onTap: (i) {
            setState(() => _currentIndex = i);
            context.go(_tabs[i]);
          },
          items: const [
            BottomNavigationBarItem(
              icon: Icon(Icons.headphones_rounded),
              label: '브리핑',
            ),
            BottomNavigationBarItem(
              icon: Icon(Icons.trending_up_rounded),
              label: '트렌드',
            ),
            BottomNavigationBarItem(
              icon: Icon(Icons.person_outline_rounded),
              label: '설정',
            ),
          ],
        ),
      ),
    );
  }
}

/// 브리핑 탭 메인 컨텐츠.
class BriefingTab extends ConsumerWidget {
  const BriefingTab({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final briefingsAsync = ref.watch(todayBriefingsProvider);
    final today = DateFormat('M월 d일 EEEE', 'ko_KR').format(DateTime.now());

    return SafeArea(
      child: RefreshIndicator(
        color: AppColors.accent,
        backgroundColor: AppColors.surfaceCard,
        onRefresh: () async {
          ref.invalidate(todayBriefingsProvider);
          ref.invalidate(unlistenedProvider);
        },
        child: CustomScrollView(
          physics: const AlwaysScrollableScrollPhysics(),
          slivers: [
            // 헤더
            SliverToBoxAdapter(
              child: Padding(
                padding: const EdgeInsets.fromLTRB(20, 16, 20, 4),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Row(
                      mainAxisAlignment: MainAxisAlignment.spaceBetween,
                      children: [
                        const Text(
                          'AudioScope',
                          style: TextStyle(
                            fontSize: 24,
                            fontWeight: FontWeight.w700,
                            color: AppColors.textPrimary,
                            letterSpacing: 0.5,
                          ),
                        ),
                        IconButton(
                          icon: const Icon(Icons.notifications_none_rounded,
                              color: AppColors.textSecondary),
                          onPressed: () {},
                        ),
                      ],
                    ),
                    Text(
                      today,
                      style: const TextStyle(
                        fontSize: 14,
                        color: AppColors.textTertiary,
                      ),
                    ),
                    const SizedBox(height: 20),

                    // 헤드라인 카드
                    _buildHeadlineCard(context),
                    const SizedBox(height: 24),

                    const Text(
                      '오늘의 브리핑',
                      style: TextStyle(
                        fontSize: 18,
                        fontWeight: FontWeight.w600,
                        color: AppColors.textPrimary,
                      ),
                    ),
                    const SizedBox(height: 12),
                  ],
                ),
              ),
            ),

            // 브리핑 카드
            briefingsAsync.when(
              data: (briefings) {
                if (briefings.isEmpty) {
                  return const SliverFillRemaining(
                    child: Center(
                      child: Column(
                        mainAxisSize: MainAxisSize.min,
                        children: [
                          Icon(Icons.headphones_rounded,
                              size: 48, color: AppColors.textTertiary),
                          SizedBox(height: 12),
                          Text(
                            '아직 생성된 브리핑이 없습니다',
                            style: TextStyle(color: AppColors.textSecondary),
                          ),
                        ],
                      ),
                    ),
                  );
                }
                return SliverList(
                  delegate: SliverChildBuilderDelegate(
                    (context, index) => Padding(
                      padding: const EdgeInsets.symmetric(
                          horizontal: 16, vertical: 6),
                      child: _BriefingCard(data: briefings[index]),
                    ),
                    childCount: briefings.length,
                  ),
                );
              },
              loading: () => const SliverFillRemaining(
                child: Center(
                  child: CircularProgressIndicator(color: AppColors.accent),
                ),
              ),
              error: (err, _) => SliverFillRemaining(
                child: Center(
                  child: Column(
                    mainAxisSize: MainAxisSize.min,
                    children: [
                      const Icon(Icons.error_outline,
                          size: 48, color: AppColors.error),
                      const SizedBox(height: 12),
                      Text('로딩 실패', style: TextStyle(color: AppColors.error)),
                      const SizedBox(height: 8),
                      OutlinedButton(
                        onPressed: () => ref.invalidate(todayBriefingsProvider),
                        child: const Text('다시 시도'),
                      ),
                    ],
                  ),
                ),
              ),
            ),

            const SliverToBoxAdapter(child: SizedBox(height: 100)),
          ],
        ),
      ),
    );
  }

  Widget _buildHeadlineCard(BuildContext context) {
    return Container(
      width: double.infinity,
      padding: const EdgeInsets.all(20),
      decoration: BoxDecoration(
        gradient: const LinearGradient(
          begin: Alignment.topLeft,
          end: Alignment.bottomRight,
          colors: [AppColors.premiumGradientStart, AppColors.premiumGradientEnd],
        ),
        borderRadius: BorderRadius.circular(20),
        border: Border.all(color: AppColors.accent.withOpacity(0.2)),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            children: [
              Container(
                padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 4),
                decoration: BoxDecoration(
                  color: AppColors.accent.withOpacity(0.2),
                  borderRadius: BorderRadius.circular(20),
                ),
                child: const Row(
                  mainAxisSize: MainAxisSize.min,
                  children: [
                    Icon(Icons.play_circle_filled_rounded,
                        size: 16, color: AppColors.accent),
                    SizedBox(width: 4),
                    Text(
                      'NOW',
                      style: TextStyle(
                        fontSize: 11,
                        fontWeight: FontWeight.w700,
                        color: AppColors.accent,
                        letterSpacing: 1,
                      ),
                    ),
                  ],
                ),
              ),
              const Spacer(),
              const Text(
                'FREE',
                style: TextStyle(
                  fontSize: 11,
                  fontWeight: FontWeight.w600,
                  color: AppColors.success,
                  letterSpacing: 1,
                ),
              ),
            ],
          ),
          const SizedBox(height: 16),
          const Text(
            '지금 듣기',
            style: TextStyle(
              fontSize: 22,
              fontWeight: FontWeight.w700,
              color: AppColors.textPrimary,
            ),
          ),
          const SizedBox(height: 4),
          Text(
            'AI 아나운서가 오늘의 핵심 뉴스를 전해드립니다',
            style: TextStyle(
              fontSize: 13,
              color: AppColors.textSecondary,
            ),
          ),
        ],
      ),
    );
  }
}

/// 브리핑 카드 위젯.
class _BriefingCard extends StatelessWidget {
  final Map<String, dynamic> data;
  const _BriefingCard({required this.data});

  @override
  Widget build(BuildContext context) {
    final period = data['period'] as String? ?? 'morning';
    final status = data['status'] as String? ?? 'pending';
    final audioUrl = data['audio_url'] as String?;
    final title = data['title'] as String? ??
        AppConstants.periodLabels[period] ?? '브리핑';
    final articleCount = data['article_count'] as int? ?? 0;
    final isLocked = data['is_locked'] == true;
    final isListened = data['is_listened'] == true;
    final isFree = data['is_free'] == true;
    final isReady = status == 'completed' && audioUrl != null;

    final periodIcon = switch (period) {
      'morning' => Icons.wb_sunny_rounded,
      'lunch' => Icons.wb_cloudy_rounded,
      'evening' => Icons.nights_stay_rounded,
      _ => Icons.radio_rounded,
    };

    return GestureDetector(
      onTap: () {
        if (isLocked) {
          context.push('/subscription');
        } else if (isReady) {
          context.push('/briefing/$period');
        }
      },
      child: Container(
        padding: const EdgeInsets.all(16),
        decoration: BoxDecoration(
          color: AppColors.surfaceCard,
          borderRadius: BorderRadius.circular(16),
          border: Border.all(
            color: isListened
                ? AppColors.surfaceLight
                : AppColors.accent.withOpacity(0.15),
          ),
        ),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              children: [
                Container(
                  width: 40,
                  height: 40,
                  decoration: BoxDecoration(
                    color: AppColors.accent.withOpacity(0.1),
                    borderRadius: BorderRadius.circular(12),
                  ),
                  child: Icon(periodIcon, color: AppColors.accent, size: 22),
                ),
                const SizedBox(width: 12),
                Expanded(
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text(
                        title,
                        style: const TextStyle(
                          fontSize: 16,
                          fontWeight: FontWeight.w600,
                          color: AppColors.textPrimary,
                        ),
                      ),
                      const SizedBox(height: 2),
                      Text(
                        '${AppConstants.periodTimes[period] ?? ''} · 기사 $articleCount건',
                        style: const TextStyle(
                          fontSize: 12,
                          color: AppColors.textTertiary,
                        ),
                      ),
                    ],
                  ),
                ),
                // 상태 표시
                if (isLocked)
                  _buildChip('PRO', AppColors.premiumGold)
                else if (isFree)
                  _buildChip('FREE', AppColors.success)
                else if (isListened)
                  _buildChip('완료', AppColors.textTertiary)
                else
                  _buildStatusChip(status),
              ],
            ),
            if (isReady && !isLocked) ...[
              const SizedBox(height: 12),
              // 재생 버튼 또는 기사 보기 선택
              Row(
                children: [
                  Expanded(
                    child: _ActionButton(
                      icon: Icons.headphones_rounded,
                      label: '오디오 브리핑',
                      onTap: () => context.push('/briefing/$period'),
                    ),
                  ),
                  const SizedBox(width: 10),
                  Expanded(
                    child: _ActionButton(
                      icon: Icons.article_outlined,
                      label: '기사 보기',
                      onTap: () => context.push('/briefing/$period?tab=articles'),
                    ),
                  ),
                ],
              ),
            ],
          ],
        ),
      ),
    );
  }

  Widget _buildChip(String label, Color color) {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 4),
      decoration: BoxDecoration(
        color: color.withOpacity(0.15),
        borderRadius: BorderRadius.circular(20),
      ),
      child: Text(
        label,
        style: TextStyle(
          fontSize: 11,
          fontWeight: FontWeight.w700,
          color: color,
          letterSpacing: 0.5,
        ),
      ),
    );
  }

  Widget _buildStatusChip(String status) {
    final (label, color) = switch (status) {
      'completed' => ('준비됨', AppColors.success),
      'generating' => ('생성중', AppColors.warning),
      'pending' => ('대기중', AppColors.accent),
      _ => ('실패', AppColors.error),
    };
    return _buildChip(label, color);
  }
}

class _ActionButton extends StatelessWidget {
  final IconData icon;
  final String label;
  final VoidCallback onTap;

  const _ActionButton({
    required this.icon,
    required this.label,
    required this.onTap,
  });

  @override
  Widget build(BuildContext context) {
    return GestureDetector(
      onTap: onTap,
      child: Container(
        padding: const EdgeInsets.symmetric(vertical: 10),
        decoration: BoxDecoration(
          color: AppColors.surfaceLight,
          borderRadius: BorderRadius.circular(10),
        ),
        child: Row(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            Icon(icon, size: 16, color: AppColors.accent),
            const SizedBox(width: 6),
            Text(
              label,
              style: const TextStyle(
                fontSize: 13,
                fontWeight: FontWeight.w500,
                color: AppColors.textPrimary,
              ),
            ),
          ],
        ),
      ),
    );
  }
}
