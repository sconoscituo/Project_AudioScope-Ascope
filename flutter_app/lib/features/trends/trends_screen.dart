import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../core/providers/providers.dart';
import '../../core/theme/app_theme.dart';

/// 주간 키워드 트렌드 화면. 워드 클라우드 + 순위 리스트.
class TrendsScreen extends ConsumerWidget {
  const TrendsScreen({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final trendsAsync = ref.watch(weeklyTrendsProvider(0));

    return SafeArea(
      child: CustomScrollView(
        slivers: [
          SliverToBoxAdapter(
            child: Padding(
              padding: const EdgeInsets.fromLTRB(20, 16, 20, 8),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  const Text(
                    '이번 주 트렌드',
                    style: TextStyle(
                      fontSize: 24,
                      fontWeight: FontWeight.w700,
                      color: AppColors.textPrimary,
                    ),
                  ),
                  const SizedBox(height: 4),
                  const Text(
                    '금주 뉴스에 가장 많이 등장한 키워드',
                    style: TextStyle(fontSize: 14, color: AppColors.textTertiary),
                  ),
                  const SizedBox(height: 20),
                ],
              ),
            ),
          ),
          trendsAsync.when(
            data: (data) {
              final words = (data['words'] as List<dynamic>?) ?? [];
              if (words.isEmpty) {
                return const SliverFillRemaining(
                  child: Center(
                    child: Text('아직 트렌드 데이터가 없습니다',
                        style: TextStyle(color: AppColors.textSecondary)),
                  ),
                );
              }

              return SliverList(
                delegate: SliverChildListDelegate([
                  // 워드 클라우드 (상위 15개 태그)
                  Padding(
                    padding: const EdgeInsets.symmetric(horizontal: 16),
                    child: _WordCloud(words: words.take(15).toList()),
                  ),
                  const SizedBox(height: 24),

                  // 순위 리스트
                  Padding(
                    padding: const EdgeInsets.symmetric(horizontal: 16),
                    child: const Text(
                      '키워드 순위',
                      style: TextStyle(
                        fontSize: 18,
                        fontWeight: FontWeight.w600,
                        color: AppColors.textPrimary,
                      ),
                    ),
                  ),
                  const SizedBox(height: 12),
                  ...words.asMap().entries.map((entry) {
                    final i = entry.key;
                    final w = entry.value as Map<String, dynamic>;
                    return _RankItem(
                      rank: i + 1,
                      word: w['word'] as String? ?? '',
                      count: w['count'] as int? ?? 0,
                      maxCount: (words.first as Map)['count'] as int? ?? 1,
                    );
                  }),
                  const SizedBox(height: 100),
                ]),
              );
            },
            loading: () => const SliverFillRemaining(
              child: Center(child: CircularProgressIndicator(color: AppColors.accent)),
            ),
            error: (_, __) => const SliverFillRemaining(
              child: Center(child: Text('로딩 실패', style: TextStyle(color: AppColors.error))),
            ),
          ),
        ],
      ),
    );
  }
}

/// 워드 클라우드 위젯 (Wrap 기반).
class _WordCloud extends StatelessWidget {
  final List<dynamic> words;
  const _WordCloud({required this.words});

  @override
  Widget build(BuildContext context) {
    final maxCount = words.isNotEmpty
        ? ((words.first as Map)['count'] as int? ?? 1)
        : 1;

    return Container(
      width: double.infinity,
      padding: const EdgeInsets.all(20),
      decoration: BoxDecoration(
        color: AppColors.surfaceCard,
        borderRadius: BorderRadius.circular(16),
      ),
      child: Wrap(
        spacing: 8,
        runSpacing: 8,
        alignment: WrapAlignment.center,
        children: words.map((w) {
          final word = (w as Map)['word'] as String? ?? '';
          final count = w['count'] as int? ?? 1;
          final ratio = count / maxCount;
          final fontSize = 14.0 + (ratio * 18.0);

          return Text(
            word,
            style: TextStyle(
              fontSize: fontSize,
              fontWeight: ratio > 0.5 ? FontWeight.w700 : FontWeight.w500,
              color: Color.lerp(
                AppColors.textTertiary,
                AppColors.accent,
                ratio,
              ),
            ),
          );
        }).toList(),
      ),
    );
  }
}

/// 키워드 순위 아이템.
class _RankItem extends StatelessWidget {
  final int rank;
  final String word;
  final int count;
  final int maxCount;

  const _RankItem({
    required this.rank,
    required this.word,
    required this.count,
    required this.maxCount,
  });

  @override
  Widget build(BuildContext context) {
    final ratio = count / maxCount;

    return Padding(
      padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 4),
      child: Container(
        padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 12),
        decoration: BoxDecoration(
          color: AppColors.surfaceCard,
          borderRadius: BorderRadius.circular(12),
        ),
        child: Row(
          children: [
            SizedBox(
              width: 32,
              child: Text(
                '$rank',
                style: TextStyle(
                  fontSize: 16,
                  fontWeight: FontWeight.w700,
                  color: rank <= 3 ? AppColors.accent : AppColors.textTertiary,
                ),
              ),
            ),
            Expanded(
              child: Text(
                word,
                style: const TextStyle(
                  fontSize: 15,
                  fontWeight: FontWeight.w500,
                  color: AppColors.textPrimary,
                ),
              ),
            ),
            // 바 그래프
            SizedBox(
              width: 80,
              child: Stack(
                children: [
                  Container(
                    height: 6,
                    decoration: BoxDecoration(
                      color: AppColors.surfaceLight,
                      borderRadius: BorderRadius.circular(3),
                    ),
                  ),
                  FractionallySizedBox(
                    widthFactor: ratio.clamp(0.05, 1.0),
                    child: Container(
                      height: 6,
                      decoration: BoxDecoration(
                        color: AppColors.accent,
                        borderRadius: BorderRadius.circular(3),
                      ),
                    ),
                  ),
                ],
              ),
            ),
            const SizedBox(width: 10),
            Text(
              '$count',
              style: const TextStyle(
                fontSize: 13,
                fontWeight: FontWeight.w600,
                color: AppColors.textSecondary,
              ),
            ),
          ],
        ),
      ),
    );
  }
}
