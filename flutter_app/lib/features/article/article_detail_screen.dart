import 'package:flutter/material.dart';
import 'package:go_router/go_router.dart';
import 'package:url_launcher/url_launcher.dart';

import '../../core/api/api_client.dart';
import '../../core/constants/app_constants.dart';
import '../../core/theme/app_theme.dart';

/// 개별 기사 상세 화면. 썸네일, 요약, 원문 링크.
class ArticleDetailScreen extends StatefulWidget {
  final String articleId;
  const ArticleDetailScreen({super.key, required this.articleId});

  @override
  State<ArticleDetailScreen> createState() => _ArticleDetailScreenState();
}

class _ArticleDetailScreenState extends State<ArticleDetailScreen> {
  Map<String, dynamic>? _article;
  bool _loading = true;

  @override
  void initState() {
    super.initState();
    _load();
  }

  Future<void> _load() async {
    try {
      final response = await ApiClient().get<Map<String, dynamic>>(
        '/api/v1/briefings/articles/${widget.articleId}',
      );
      final data = ApiClient.extractData<Map<String, dynamic>>(response);
      if (mounted) setState(() { _article = data; _loading = false; });
    } catch (_) {
      if (mounted) setState(() => _loading = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: AppColors.primary,
      appBar: AppBar(
        title: const Text('기사 상세'),
        leading: IconButton(
          icon: const Icon(Icons.arrow_back_ios_new_rounded, size: 20),
          onPressed: () => context.pop(),
        ),
      ),
      body: _loading
          ? const Center(child: CircularProgressIndicator(color: AppColors.accent))
          : _article == null
              ? const Center(child: Text('기사를 찾을 수 없습니다', style: TextStyle(color: AppColors.textSecondary)))
              : _buildContent(),
    );
  }

  Widget _buildContent() {
    final a = _article!;
    final thumbnailUrl = a['thumbnail_url'] as String?;
    final videoUrl = a['video_url'] as String?;
    final category = a['category'] as String?;

    return SingleChildScrollView(
      padding: const EdgeInsets.all(20),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          // 썸네일
          if (thumbnailUrl != null) ...[
            ClipRRect(
              borderRadius: BorderRadius.circular(16),
              child: Image.network(
                thumbnailUrl,
                width: double.infinity,
                height: 200,
                fit: BoxFit.cover,
                errorBuilder: (_, __, ___) => const SizedBox(),
              ),
            ),
            const SizedBox(height: 20),
          ],

          // 카테고리
          if (category != null)
            Container(
              padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 4),
              decoration: BoxDecoration(
                color: AppColors.categoryColor(category).withOpacity(0.15),
                borderRadius: BorderRadius.circular(20),
              ),
              child: Text(
                AppConstants.categoryLabels[category] ?? category,
                style: TextStyle(
                  fontSize: 12,
                  fontWeight: FontWeight.w600,
                  color: AppColors.categoryColor(category),
                ),
              ),
            ),
          const SizedBox(height: 12),

          // 제목
          Text(
            a['title'] as String? ?? '',
            style: const TextStyle(
              fontSize: 22,
              fontWeight: FontWeight.w700,
              color: AppColors.textPrimary,
              height: 1.4,
            ),
          ),
          const SizedBox(height: 8),

          // 출처
          Text(
            a['source'] as String? ?? '',
            style: const TextStyle(fontSize: 13, color: AppColors.textTertiary),
          ),
          const SizedBox(height: 20),

          // 요약
          if ((a['summary'] as String?)?.isNotEmpty == true) ...[
            Container(
              width: double.infinity,
              padding: const EdgeInsets.all(16),
              decoration: BoxDecoration(
                color: AppColors.surfaceCard,
                borderRadius: BorderRadius.circular(12),
                border: Border.all(color: AppColors.accent.withOpacity(0.2)),
              ),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  const Row(
                    children: [
                      Icon(Icons.auto_awesome, size: 16, color: AppColors.accent),
                      SizedBox(width: 6),
                      Text('AI 요약', style: TextStyle(fontSize: 13, fontWeight: FontWeight.w600, color: AppColors.accent)),
                    ],
                  ),
                  const SizedBox(height: 10),
                  Text(
                    a['summary'] as String,
                    style: const TextStyle(
                      fontSize: 15,
                      color: AppColors.textPrimary,
                      height: 1.7,
                    ),
                  ),
                ],
              ),
            ),
            const SizedBox(height: 20),
          ],

          // 전체 내용
          if ((a['full_content'] as String?)?.isNotEmpty == true) ...[
            Text(
              a['full_content'] as String,
              style: const TextStyle(
                fontSize: 15,
                color: AppColors.textSecondary,
                height: 1.8,
              ),
            ),
            const SizedBox(height: 20),
          ],

          // 영상 링크
          if (videoUrl != null) ...[
            GestureDetector(
              onTap: () => launchUrl(Uri.parse(videoUrl)),
              child: Container(
                padding: const EdgeInsets.all(14),
                decoration: BoxDecoration(
                  color: AppColors.surfaceCard,
                  borderRadius: BorderRadius.circular(12),
                ),
                child: const Row(
                  children: [
                    Icon(Icons.play_circle_outline, color: AppColors.accent),
                    SizedBox(width: 10),
                    Text('관련 영상 보기', style: TextStyle(color: AppColors.accent, fontWeight: FontWeight.w600)),
                  ],
                ),
              ),
            ),
            const SizedBox(height: 16),
          ],

          // 원문 보기
          SizedBox(
            width: double.infinity,
            child: OutlinedButton.icon(
              onPressed: () {
                final url = a['original_url'] as String?;
                if (url != null) launchUrl(Uri.parse(url), mode: LaunchMode.externalApplication);
              },
              icon: const Icon(Icons.open_in_new_rounded, size: 18),
              label: const Text('원문 기사 보기'),
            ),
          ),
          const SizedBox(height: 40),
        ],
      ),
    );
  }
}
