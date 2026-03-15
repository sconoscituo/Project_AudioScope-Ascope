import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import '../../core/api/api_client.dart';
import '../../core/constants/app_constants.dart';
import '../../core/theme/app_theme.dart';
import 'audio_player_widget.dart';

/// 특정 시간대 브리핑 상세 화면.
/// 오디오 재생 + 기사 목록 (탭 전환).
class BriefingDetailScreen extends ConsumerStatefulWidget {
  final String period;
  final String? initialTab;

  const BriefingDetailScreen({
    super.key,
    required this.period,
    this.initialTab,
  });

  @override
  ConsumerState<BriefingDetailScreen> createState() =>
      _BriefingDetailScreenState();
}

class _BriefingDetailScreenState extends ConsumerState<BriefingDetailScreen>
    with SingleTickerProviderStateMixin {
  late final TabController _tabController;
  Map<String, dynamic>? _briefing;
  bool _loading = true;
  String? _error;

  @override
  void initState() {
    super.initState();
    _tabController = TabController(
      length: 2,
      vsync: this,
      initialIndex: widget.initialTab == 'articles' ? 1 : 0,
    );
    _loadBriefing();
  }

  Future<void> _loadBriefing() async {
    try {
      final response = await ApiClient().get<Map<String, dynamic>>(
        '/api/v1/briefings/${widget.period}',
      );
      final data = ApiClient.extractData<Map<String, dynamic>>(response);
      if (mounted) setState(() { _briefing = data; _loading = false; });
    } catch (e) {
      if (mounted) setState(() { _error = e.toString(); _loading = false; });
    }
  }

  @override
  void dispose() {
    _tabController.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final title = AppConstants.periodLabels[widget.period] ?? '브리핑';

    return Scaffold(
      backgroundColor: AppColors.primary,
      appBar: AppBar(
        title: Text(title),
        leading: IconButton(
          icon: const Icon(Icons.arrow_back_ios_new_rounded, size: 20),
          onPressed: () => context.pop(),
        ),
        bottom: TabBar(
          controller: _tabController,
          indicatorColor: AppColors.accent,
          labelColor: AppColors.accent,
          unselectedLabelColor: AppColors.textTertiary,
          tabs: const [
            Tab(text: '오디오 브리핑'),
            Tab(text: '기사 목록'),
          ],
        ),
      ),
      body: _loading
          ? const Center(child: CircularProgressIndicator(color: AppColors.accent))
          : _error != null
              ? Center(child: Text('로딩 실패', style: TextStyle(color: AppColors.error)))
              : TabBarView(
                  controller: _tabController,
                  children: [
                    _AudioTab(briefing: _briefing!),
                    _ArticlesTab(briefing: _briefing!),
                  ],
                ),
    );
  }
}

/// 오디오 재생 탭.
class _AudioTab extends StatelessWidget {
  final Map<String, dynamic> briefing;
  const _AudioTab({required this.briefing});

  @override
  Widget build(BuildContext context) {
    final audioUrl = briefing['audio_url'] as String?;
    final script = briefing['script'] as String?;
    final articleCount = briefing['article_count'] as int? ?? 0;
    final duration = briefing['audio_duration_seconds'] as int?;

    return SingleChildScrollView(
      padding: const EdgeInsets.all(20),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          // 재생 카드
          Container(
            width: double.infinity,
            padding: const EdgeInsets.all(24),
            decoration: BoxDecoration(
              gradient: const LinearGradient(
                begin: Alignment.topLeft,
                end: Alignment.bottomRight,
                colors: [AppColors.premiumGradientStart, AppColors.surfaceCard],
              ),
              borderRadius: BorderRadius.circular(20),
              border: Border.all(color: AppColors.accent.withOpacity(0.2)),
            ),
            child: Column(
              children: [
                // 큰 헤드셋 아이콘
                Container(
                  width: 80,
                  height: 80,
                  decoration: BoxDecoration(
                    shape: BoxShape.circle,
                    color: AppColors.accent.withOpacity(0.15),
                  ),
                  child: const Icon(
                    Icons.headphones_rounded,
                    size: 40,
                    color: AppColors.accent,
                  ),
                ),
                const SizedBox(height: 16),
                Text(
                  briefing['title'] as String? ?? '오늘의 브리핑',
                  style: const TextStyle(
                    fontSize: 20,
                    fontWeight: FontWeight.w700,
                    color: AppColors.textPrimary,
                  ),
                ),
                const SizedBox(height: 4),
                Text(
                  '기사 $articleCount건${duration != null ? ' · ${(duration / 60).ceil()}분' : ''}',
                  style: const TextStyle(
                    fontSize: 13,
                    color: AppColors.textTertiary,
                  ),
                ),
                const SizedBox(height: 20),
                if (audioUrl != null)
                  AudioPlayerWidget(
                    audioUrl: audioUrl,
                    briefingId: briefing['id'] as String? ?? '',
                  ),
              ],
            ),
          ),
          const SizedBox(height: 24),

          // 스크립트 (눈으로 보기)
          if (script != null && script.isNotEmpty) ...[
            const Text(
              '브리핑 스크립트',
              style: TextStyle(
                fontSize: 16,
                fontWeight: FontWeight.w600,
                color: AppColors.textPrimary,
              ),
            ),
            const SizedBox(height: 12),
            Container(
              width: double.infinity,
              padding: const EdgeInsets.all(16),
              decoration: BoxDecoration(
                color: AppColors.surfaceCard,
                borderRadius: BorderRadius.circular(12),
              ),
              child: Text(
                script,
                style: const TextStyle(
                  fontSize: 15,
                  color: AppColors.textSecondary,
                  height: 1.8,
                ),
              ),
            ),
          ],
        ],
      ),
    );
  }
}

/// 기사 목록 탭.
class _ArticlesTab extends StatelessWidget {
  final Map<String, dynamic> briefing;
  const _ArticlesTab({required this.briefing});

  @override
  Widget build(BuildContext context) {
    final articles = (briefing['articles'] as List<dynamic>?) ?? [];

    if (articles.isEmpty) {
      return const Center(
        child: Text('기사가 없습니다', style: TextStyle(color: AppColors.textSecondary)),
      );
    }

    return ListView.builder(
      padding: const EdgeInsets.all(16),
      itemCount: articles.length,
      itemBuilder: (context, index) {
        final article = articles[index] as Map<String, dynamic>;
        return _ArticleCard(article: article, index: index);
      },
    );
  }
}

class _ArticleCard extends StatelessWidget {
  final Map<String, dynamic> article;
  final int index;

  const _ArticleCard({required this.article, required this.index});

  @override
  Widget build(BuildContext context) {
    final title = article['title'] as String? ?? '';
    final summary = article['summary'] as String? ?? '';
    final source = article['source'] as String? ?? '';
    final category = article['category'] as String?;
    final thumbnailUrl = article['thumbnail_url'] as String?;

    return GestureDetector(
      onTap: () {
        final id = article['id'];
        if (id != null) context.push('/article/$id');
      },
      child: Container(
        margin: const EdgeInsets.only(bottom: 12),
        padding: const EdgeInsets.all(14),
        decoration: BoxDecoration(
          color: AppColors.surfaceCard,
          borderRadius: BorderRadius.circular(14),
        ),
        child: Row(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            // 번호
            Container(
              width: 28,
              height: 28,
              decoration: BoxDecoration(
                color: AppColors.accent.withOpacity(0.1),
                borderRadius: BorderRadius.circular(8),
              ),
              child: Center(
                child: Text(
                  '${index + 1}',
                  style: const TextStyle(
                    fontSize: 13,
                    fontWeight: FontWeight.w700,
                    color: AppColors.accent,
                  ),
                ),
              ),
            ),
            const SizedBox(width: 12),
            Expanded(
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  if (category != null) ...[
                    Text(
                      AppConstants.categoryLabels[category] ?? category,
                      style: TextStyle(
                        fontSize: 11,
                        fontWeight: FontWeight.w600,
                        color: AppColors.categoryColor(category),
                      ),
                    ),
                    const SizedBox(height: 4),
                  ],
                  Text(
                    title,
                    style: const TextStyle(
                      fontSize: 15,
                      fontWeight: FontWeight.w600,
                      color: AppColors.textPrimary,
                      height: 1.4,
                    ),
                    maxLines: 2,
                    overflow: TextOverflow.ellipsis,
                  ),
                  if (summary.isNotEmpty) ...[
                    const SizedBox(height: 6),
                    Text(
                      summary,
                      style: const TextStyle(
                        fontSize: 13,
                        color: AppColors.textSecondary,
                        height: 1.5,
                      ),
                      maxLines: 2,
                      overflow: TextOverflow.ellipsis,
                    ),
                  ],
                  if (source.isNotEmpty) ...[
                    const SizedBox(height: 6),
                    Text(
                      source,
                      style: const TextStyle(
                        fontSize: 11,
                        color: AppColors.textTertiary,
                      ),
                    ),
                  ],
                ],
              ),
            ),
            if (thumbnailUrl != null) ...[
              const SizedBox(width: 10),
              ClipRRect(
                borderRadius: BorderRadius.circular(8),
                child: Image.network(
                  thumbnailUrl,
                  width: 70,
                  height: 70,
                  fit: BoxFit.cover,
                  errorBuilder: (_, __, ___) => const SizedBox(),
                ),
              ),
            ],
          ],
        ),
      ),
    );
  }
}
