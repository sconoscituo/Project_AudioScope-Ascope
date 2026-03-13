import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import 'package:intl/intl.dart';

import '../../core/api/api_client.dart';
import '../../core/auth/auth_service.dart';
import 'audio_player_widget.dart';

/// 브리핑 데이터 모델.
class BriefingItem {
  final String id;
  final String period;
  final String periodLabel;
  final String? audioUrl;
  final String status;
  final int articleCount;
  final DateTime? generatedAt;

  const BriefingItem({
    required this.id,
    required this.period,
    required this.periodLabel,
    this.audioUrl,
    required this.status,
    required this.articleCount,
    this.generatedAt,
  });

  factory BriefingItem.fromJson(Map<String, dynamic> json) {
    const periodLabels = {
      'morning': '아침 브리핑',
      'lunch': '점심 브리핑',
      'evening': '저녁 브리핑',
    };
    return BriefingItem(
      id: json['id'] as String,
      period: json['period'] as String,
      periodLabel: periodLabels[json['period']] ?? json['period'] as String,
      audioUrl: json['audio_url'] as String?,
      status: json['status'] as String,
      articleCount: json['article_count'] as int? ?? 0,
      generatedAt: json['generated_at'] != null
          ? DateTime.tryParse(json['generated_at'] as String)
          : null,
    );
  }
}

/// 오늘의 브리핑 목록을 로드하는 Provider.
final todayBriefingsProvider =
    FutureProvider<List<BriefingItem>>((ref) async {
  final response = await ApiClient().get<Map<String, dynamic>>(
    '/api/v1/briefings/today',
  );
  final data = response.data?['data'] as List<dynamic>? ?? [];
  return data
      .map((item) => BriefingItem.fromJson(item as Map<String, dynamic>))
      .toList();
});

/// 메인 브리핑 화면.
/// 오늘의 아침/점심/저녁 3개 브리핑 카드를 표시합니다.
class BriefingScreen extends ConsumerWidget {
  const BriefingScreen({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final briefingsAsync = ref.watch(todayBriefingsProvider);
    final today = DateFormat('yyyy년 M월 d일 (E)', 'ko_KR').format(DateTime.now());

    return Scaffold(
      appBar: AppBar(
        title: const Text('AudioScope'),
        centerTitle: false,
        actions: [
          IconButton(
            icon: const Icon(Icons.logout),
            tooltip: '로그아웃',
            onPressed: () async {
              await AuthService.instance.signOut();
              if (context.mounted) context.go('/login');
            },
          ),
        ],
      ),
      body: RefreshIndicator(
        onRefresh: () async => ref.invalidate(todayBriefingsProvider),
        child: CustomScrollView(
          slivers: [
            SliverToBoxAdapter(
              child: Padding(
                padding: const EdgeInsets.fromLTRB(20, 20, 20, 8),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(
                      today,
                      style: Theme.of(context).textTheme.bodyMedium?.copyWith(
                            color: Theme.of(context).colorScheme.outline,
                          ),
                    ),
                    const SizedBox(height: 4),
                    Text(
                      '오늘의 뉴스 브리핑',
                      style: Theme.of(context).textTheme.headlineSmall?.copyWith(
                            fontWeight: FontWeight.bold,
                          ),
                    ),
                  ],
                ),
              ),
            ),
            briefingsAsync.when(
              data: (briefings) => briefings.isEmpty
                  ? const SliverFillRemaining(
                      child: Center(
                        child: Text('아직 생성된 브리핑이 없습니다.\n잠시 후 다시 확인해주세요.'),
                      ),
                    )
                  : SliverList(
                      delegate: SliverChildBuilderDelegate(
                        (context, index) => Padding(
                          padding: const EdgeInsets.symmetric(
                              horizontal: 16, vertical: 8),
                          child: _BriefingCard(item: briefings[index]),
                        ),
                        childCount: briefings.length,
                      ),
                    ),
              loading: () => const SliverFillRemaining(
                child: Center(child: CircularProgressIndicator()),
              ),
              error: (error, _) => SliverFillRemaining(
                child: Center(
                  child: Column(
                    mainAxisSize: MainAxisSize.min,
                    children: [
                      const Icon(Icons.error_outline, size: 48, color: Colors.red),
                      const SizedBox(height: 12),
                      Text('불러오기 실패: $error'),
                      const SizedBox(height: 12),
                      ElevatedButton(
                        onPressed: () => ref.invalidate(todayBriefingsProvider),
                        child: const Text('다시 시도'),
                      ),
                    ],
                  ),
                ),
              ),
            ),
          ],
        ),
      ),
    );
  }
}

/// 개별 브리핑 카드 위젯.
class _BriefingCard extends StatelessWidget {
  final BriefingItem item;

  const _BriefingCard({required this.item});

  IconData get _periodIcon {
    switch (item.period) {
      case 'morning':
        return Icons.wb_sunny_outlined;
      case 'lunch':
        return Icons.wb_cloudy_outlined;
      case 'evening':
        return Icons.nights_stay_outlined;
      default:
        return Icons.radio_outlined;
    }
  }

  @override
  Widget build(BuildContext context) {
    final isReady = item.status == 'completed' && item.audioUrl != null;
    final isGenerating = item.status == 'generating' || item.status == 'pending';

    return Card(
      elevation: 2,
      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(16)),
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              children: [
                Icon(_periodIcon,
                    color: Theme.of(context).colorScheme.primary),
                const SizedBox(width: 8),
                Text(
                  item.periodLabel,
                  style: Theme.of(context).textTheme.titleMedium?.copyWith(
                        fontWeight: FontWeight.bold,
                      ),
                ),
                const Spacer(),
                _StatusChip(status: item.status),
              ],
            ),
            if (item.articleCount > 0) ...[
              const SizedBox(height: 6),
              Text(
                '기사 ${item.articleCount}건 요약',
                style: Theme.of(context).textTheme.bodySmall?.copyWith(
                      color: Theme.of(context).colorScheme.outline,
                    ),
              ),
            ],
            const SizedBox(height: 12),
            if (isReady)
              AudioPlayerWidget(audioUrl: item.audioUrl!)
            else if (isGenerating)
              const Row(
                children: [
                  SizedBox(
                    width: 16,
                    height: 16,
                    child: CircularProgressIndicator(strokeWidth: 2),
                  ),
                  SizedBox(width: 8),
                  Text('브리핑 생성 중...'),
                ],
              )
            else
              Text(
                '브리핑을 준비하지 못했습니다.',
                style: TextStyle(
                    color: Theme.of(context).colorScheme.error),
              ),
          ],
        ),
      ),
    );
  }
}

/// 브리핑 상태 표시 칩.
class _StatusChip extends StatelessWidget {
  final String status;

  const _StatusChip({required this.status});

  @override
  Widget build(BuildContext context) {
    final (label, color) = switch (status) {
      'completed' => ('완료', Colors.green),
      'generating' => ('생성중', Colors.orange),
      'pending' => ('대기중', Colors.blue),
      _ => ('실패', Colors.red),
    };

    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 3),
      decoration: BoxDecoration(
        color: color.withOpacity(0.15),
        borderRadius: BorderRadius.circular(12),
      ),
      child: Text(
        label,
        style: TextStyle(
            fontSize: 11, color: color, fontWeight: FontWeight.w600),
      ),
    );
  }
}
