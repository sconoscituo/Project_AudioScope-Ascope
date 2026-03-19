import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../core/api/api_client.dart';
import '../../core/theme/app_theme.dart';

// ── Providers ───────────────────────────────────────────────────────────────

/// 총 청취 통계 Provider.
final listeningStatsProvider =
    FutureProvider.autoDispose<Map<String, dynamic>>((ref) async {
  final response = await ApiClient().get<Map<String, dynamic>>(
    '/api/v1/stats/listening',
  );
  return ApiClient.extractData<Map<String, dynamic>>(response) ?? {};
});

/// 주간 청취 통계 Provider.
final weeklyListeningProvider =
    FutureProvider.autoDispose<List<Map<String, dynamic>>>((ref) async {
  final response = await ApiClient().get<Map<String, dynamic>>(
    '/api/v1/stats/listening/weekly',
  );
  final data = ApiClient.extractData<List<dynamic>>(response);
  return data?.cast<Map<String, dynamic>>() ?? [];
});

// ── Screen ───────────────────────────────────────────────────────────────────

/// 통계 화면. 청취 시간 / 스트릭 / 주간 차트.
class StatsScreen extends ConsumerWidget {
  const StatsScreen({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final statsAsync = ref.watch(listeningStatsProvider);
    final weeklyAsync = ref.watch(weeklyListeningProvider);

    return Scaffold(
      backgroundColor: AppColors.primary,
      appBar: AppBar(
        title: const Text('청취 통계'),
        backgroundColor: AppColors.surface,
        actions: [
          IconButton(
            icon: const Icon(Icons.refresh_rounded, color: AppColors.textSecondary),
            onPressed: () {
              ref.invalidate(listeningStatsProvider);
              ref.invalidate(weeklyListeningProvider);
            },
          ),
        ],
        bottom: PreferredSize(
          preferredSize: const Size.fromHeight(0.5),
          child: Container(color: AppColors.surfaceLight, height: 0.5),
        ),
      ),
      body: RefreshIndicator(
        color: AppColors.accent,
        backgroundColor: AppColors.surfaceCard,
        onRefresh: () async {
          ref.invalidate(listeningStatsProvider);
          ref.invalidate(weeklyListeningProvider);
        },
        child: SingleChildScrollView(
          physics: const AlwaysScrollableScrollPhysics(),
          padding: const EdgeInsets.all(16),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              // 상단 요약 카드 행
              statsAsync.when(
                data: (stats) => _SummaryRow(stats: stats),
                loading: () => _SummaryRowSkeleton(),
                error: (_, __) => _ErrorCard(
                  onRetry: () => ref.invalidate(listeningStatsProvider),
                ),
              ),

              const SizedBox(height: 24),

              // 주간 청취 차트
              const Text(
                '이번 주 청취 현황',
                style: TextStyle(
                  fontSize: 16,
                  fontWeight: FontWeight.w600,
                  color: AppColors.textPrimary,
                ),
              ),
              const SizedBox(height: 12),
              weeklyAsync.when(
                data: (weekly) => _WeeklyBarChart(data: weekly),
                loading: () => _BarChartSkeleton(),
                error: (_, __) => _ErrorCard(
                  onRetry: () => ref.invalidate(weeklyListeningProvider),
                ),
              ),

              const SizedBox(height: 24),

              // 추가 통계 (총계)
              statsAsync.when(
                data: (stats) => _DetailStats(stats: stats),
                loading: () => const SizedBox.shrink(),
                error: (_, __) => const SizedBox.shrink(),
              ),

              const SizedBox(height: 32),
            ],
          ),
        ),
      ),
    );
  }
}

// ── Summary Row ──────────────────────────────────────────────────────────────

class _SummaryRow extends StatelessWidget {
  final Map<String, dynamic> stats;
  const _SummaryRow({required this.stats});

  @override
  Widget build(BuildContext context) {
    final totalMinutes = (stats['total_listening_minutes'] as num?)?.toInt() ?? 0;
    final streakDays = (stats['streak_days'] as num?)?.toInt() ?? 0;
    final totalBriefings = (stats['total_briefings_listened'] as num?)?.toInt() ?? 0;

    final hours = totalMinutes ~/ 60;
    final mins = totalMinutes % 60;
    final timeLabel = hours > 0 ? '${hours}시간 ${mins}분' : '${mins}분';

    return Row(
      children: [
        Expanded(
          child: _StatCard(
            icon: Icons.headphones_rounded,
            label: '총 청취 시간',
            value: timeLabel,
            iconColor: AppColors.accent,
          ),
        ),
        const SizedBox(width: 12),
        Expanded(
          child: _StatCard(
            icon: Icons.local_fire_department_rounded,
            label: '연속 청취',
            value: '$streakDays일',
            iconColor: AppColors.warning,
          ),
        ),
        const SizedBox(width: 12),
        Expanded(
          child: _StatCard(
            icon: Icons.library_music_rounded,
            label: '총 브리핑',
            value: '$totalBriefings건',
            iconColor: AppColors.categoryTech,
          ),
        ),
      ],
    );
  }
}

class _StatCard extends StatelessWidget {
  final IconData icon;
  final String label;
  final String value;
  final Color iconColor;

  const _StatCard({
    required this.icon,
    required this.label,
    required this.value,
    required this.iconColor,
  });

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 16),
      decoration: BoxDecoration(
        color: AppColors.surfaceCard,
        borderRadius: BorderRadius.circular(16),
        border: Border.all(color: AppColors.surfaceLight),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Container(
            width: 36,
            height: 36,
            decoration: BoxDecoration(
              color: iconColor.withOpacity(0.1),
              borderRadius: BorderRadius.circular(10),
            ),
            child: Icon(icon, size: 18, color: iconColor),
          ),
          const SizedBox(height: 12),
          Text(
            value,
            style: const TextStyle(
              fontSize: 18,
              fontWeight: FontWeight.w700,
              color: AppColors.textPrimary,
            ),
          ),
          const SizedBox(height: 2),
          Text(
            label,
            style: const TextStyle(
              fontSize: 11,
              color: AppColors.textTertiary,
            ),
          ),
        ],
      ),
    );
  }
}

// ── Weekly Bar Chart ─────────────────────────────────────────────────────────

class _WeeklyBarChart extends StatelessWidget {
  final List<Map<String, dynamic>> data;
  const _WeeklyBarChart({required this.data});

  static const _dayLabels = ['월', '화', '수', '목', '금', '토', '일'];

  @override
  Widget build(BuildContext context) {
    if (data.isEmpty) {
      return Container(
        height: 160,
        decoration: BoxDecoration(
          color: AppColors.surfaceCard,
          borderRadius: BorderRadius.circular(16),
          border: Border.all(color: AppColors.surfaceLight),
        ),
        child: const Center(
          child: Text(
            '이번 주 청취 데이터가 없습니다',
            style: TextStyle(color: AppColors.textTertiary, fontSize: 13),
          ),
        ),
      );
    }

    // 최대값 계산 (막대 높이 정규화)
    final maxMinutes = data
        .map((d) => (d['minutes'] as num?)?.toDouble() ?? 0.0)
        .fold(0.0, (a, b) => a > b ? a : b);
    final effectiveMax = maxMinutes < 1 ? 1.0 : maxMinutes;

    return Container(
      padding: const EdgeInsets.fromLTRB(16, 20, 16, 12),
      decoration: BoxDecoration(
        color: AppColors.surfaceCard,
        borderRadius: BorderRadius.circular(16),
        border: Border.all(color: AppColors.surfaceLight),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          SizedBox(
            height: 120,
            child: Row(
              crossAxisAlignment: CrossAxisAlignment.end,
              children: List.generate(data.length > 7 ? 7 : data.length, (i) {
                final item = data[i];
                final minutes = (item['minutes'] as num?)?.toDouble() ?? 0.0;
                final ratio = minutes / effectiveMax;
                final isToday = item['is_today'] == true;

                return Expanded(
                  child: Padding(
                    padding: const EdgeInsets.symmetric(horizontal: 4),
                    child: Column(
                      mainAxisAlignment: MainAxisAlignment.end,
                      children: [
                        if (minutes > 0)
                          Padding(
                            padding: const EdgeInsets.only(bottom: 4),
                            child: Text(
                              _formatMinutes(minutes.toInt()),
                              style: TextStyle(
                                fontSize: 9,
                                color: isToday
                                    ? AppColors.accent
                                    : AppColors.textTertiary,
                                fontWeight: isToday
                                    ? FontWeight.w700
                                    : FontWeight.w400,
                              ),
                            ),
                          ),
                        AnimatedContainer(
                          duration: Duration(milliseconds: 400 + i * 60),
                          curve: Curves.easeOutCubic,
                          height: ratio * 90,
                          decoration: BoxDecoration(
                            color: isToday
                                ? AppColors.accent
                                : AppColors.accent.withOpacity(0.35),
                            borderRadius: const BorderRadius.vertical(
                              top: Radius.circular(5),
                            ),
                          ),
                        ),
                      ],
                    ),
                  ),
                );
              }),
            ),
          ),
          const SizedBox(height: 8),
          // 요일 레이블
          Row(
            children: List.generate(data.length > 7 ? 7 : data.length, (i) {
              final item = data[i];
              final isToday = item['is_today'] == true;
              final dayLabel = item['day_label'] as String? ??
                  (i < _dayLabels.length ? _dayLabels[i] : '');

              return Expanded(
                child: Center(
                  child: Text(
                    dayLabel,
                    style: TextStyle(
                      fontSize: 11,
                      fontWeight:
                          isToday ? FontWeight.w700 : FontWeight.w400,
                      color: isToday ? AppColors.accent : AppColors.textTertiary,
                    ),
                  ),
                ),
              );
            }),
          ),
        ],
      ),
    );
  }

  String _formatMinutes(int minutes) {
    if (minutes < 60) return '${minutes}m';
    return '${minutes ~/ 60}h${minutes % 60 > 0 ? ' ${minutes % 60}m' : ''}';
  }
}

// ── Detail Stats ─────────────────────────────────────────────────────────────

class _DetailStats extends StatelessWidget {
  final Map<String, dynamic> stats;
  const _DetailStats({required this.stats});

  @override
  Widget build(BuildContext context) {
    final avgPerDay =
        (stats['avg_minutes_per_day'] as num?)?.toDouble() ?? 0.0;
    final favoritesCount =
        (stats['favorites_count'] as num?)?.toInt() ?? 0;
    final longestStreak =
        (stats['longest_streak_days'] as num?)?.toInt() ?? 0;

    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        const Text(
          '상세 통계',
          style: TextStyle(
            fontSize: 16,
            fontWeight: FontWeight.w600,
            color: AppColors.textPrimary,
          ),
        ),
        const SizedBox(height: 12),
        Container(
          decoration: BoxDecoration(
            color: AppColors.surfaceCard,
            borderRadius: BorderRadius.circular(16),
            border: Border.all(color: AppColors.surfaceLight),
          ),
          child: Column(
            children: [
              _DetailRow(
                icon: Icons.timer_outlined,
                label: '일평균 청취 시간',
                value: '${avgPerDay.toStringAsFixed(1)}분',
                isFirst: true,
              ),
              _Divider(),
              _DetailRow(
                icon: Icons.bookmark_outline_rounded,
                label: '즐겨찾기 기사',
                value: '$favoritesCount건',
              ),
              _Divider(),
              _DetailRow(
                icon: Icons.emoji_events_outlined,
                label: '최장 연속 청취',
                value: '$longestStreak일',
                isLast: true,
              ),
            ],
          ),
        ),
      ],
    );
  }
}

class _DetailRow extends StatelessWidget {
  final IconData icon;
  final String label;
  final String value;
  final bool isFirst;
  final bool isLast;

  const _DetailRow({
    required this.icon,
    required this.label,
    required this.value,
    this.isFirst = false,
    this.isLast = false,
  });

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: EdgeInsets.fromLTRB(
        16,
        isFirst ? 16 : 12,
        16,
        isLast ? 16 : 12,
      ),
      child: Row(
        children: [
          Icon(icon, size: 18, color: AppColors.textTertiary),
          const SizedBox(width: 12),
          Expanded(
            child: Text(
              label,
              style: const TextStyle(
                fontSize: 14,
                color: AppColors.textSecondary,
              ),
            ),
          ),
          Text(
            value,
            style: const TextStyle(
              fontSize: 14,
              fontWeight: FontWeight.w600,
              color: AppColors.textPrimary,
            ),
          ),
        ],
      ),
    );
  }
}

class _Divider extends StatelessWidget {
  @override
  Widget build(BuildContext context) {
    return Container(
      height: 0.5,
      margin: const EdgeInsets.symmetric(horizontal: 16),
      color: AppColors.surfaceLight,
    );
  }
}

// ── Skeletons / Error ─────────────────────────────────────────────────────────

class _SummaryRowSkeleton extends StatelessWidget {
  @override
  Widget build(BuildContext context) {
    return Row(
      children: List.generate(3, (i) {
        return Expanded(
          child: Container(
            margin: EdgeInsets.only(left: i > 0 ? 12 : 0),
            height: 110,
            decoration: BoxDecoration(
              color: AppColors.surfaceCard,
              borderRadius: BorderRadius.circular(16),
            ),
          ),
        );
      }),
    );
  }
}

class _BarChartSkeleton extends StatelessWidget {
  @override
  Widget build(BuildContext context) {
    return Container(
      height: 160,
      decoration: BoxDecoration(
        color: AppColors.surfaceCard,
        borderRadius: BorderRadius.circular(16),
      ),
      child: const Center(
        child: CircularProgressIndicator(color: AppColors.accent),
      ),
    );
  }
}

class _ErrorCard extends StatelessWidget {
  final VoidCallback onRetry;
  const _ErrorCard({required this.onRetry});

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.all(20),
      decoration: BoxDecoration(
        color: AppColors.surfaceCard,
        borderRadius: BorderRadius.circular(16),
        border: Border.all(color: AppColors.error.withOpacity(0.3)),
      ),
      child: Row(
        children: [
          const Icon(Icons.error_outline, color: AppColors.error, size: 20),
          const SizedBox(width: 12),
          const Expanded(
            child: Text(
              '데이터를 불러오지 못했습니다',
              style: TextStyle(color: AppColors.textSecondary, fontSize: 13),
            ),
          ),
          TextButton(
            onPressed: onRetry,
            child: const Text('재시도', style: TextStyle(color: AppColors.accent)),
          ),
        ],
      ),
    );
  }
}
