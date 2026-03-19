import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import 'package:intl/intl.dart';

import '../../core/theme/app_theme.dart';
import 'favorites_provider.dart';

/// 즐겨찾기 화면. 저장된 기사 목록 표시.
class FavoritesScreen extends ConsumerWidget {
  const FavoritesScreen({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final favoritesAsync = ref.watch(favoritesProvider);
    final removeState = ref.watch(favoritesNotifierProvider);

    return Scaffold(
      backgroundColor: AppColors.primary,
      appBar: AppBar(
        title: const Text('즐겨찾기'),
        backgroundColor: AppColors.surface,
        bottom: PreferredSize(
          preferredSize: const Size.fromHeight(0.5),
          child: Container(color: AppColors.surfaceLight, height: 0.5),
        ),
      ),
      body: Stack(
        children: [
          favoritesAsync.when(
            data: (favorites) {
              if (favorites.isEmpty) {
                return _EmptyState();
              }
              return RefreshIndicator(
                color: AppColors.accent,
                backgroundColor: AppColors.surfaceCard,
                onRefresh: () async => ref.invalidate(favoritesProvider),
                child: ListView.builder(
                  padding: const EdgeInsets.symmetric(
                    horizontal: 16,
                    vertical: 12,
                  ),
                  itemCount: favorites.length,
                  itemBuilder: (context, index) {
                    final item = favorites[index];
                    return _FavoriteItem(
                      item: item,
                      onDelete: () {
                        final id = item['id']?.toString();
                        if (id != null) {
                          ref
                              .read(favoritesNotifierProvider.notifier)
                              .removeFavorite(id);
                        }
                      },
                      onTap: () {
                        final articleId = item['article_id']?.toString() ??
                            item['id']?.toString();
                        if (articleId != null) {
                          context.push('/article/$articleId');
                        }
                      },
                    );
                  },
                ),
              );
            },
            loading: () => const Center(
              child: CircularProgressIndicator(color: AppColors.accent),
            ),
            error: (err, _) => Center(
              child: Column(
                mainAxisSize: MainAxisSize.min,
                children: [
                  const Icon(
                    Icons.error_outline,
                    size: 48,
                    color: AppColors.error,
                  ),
                  const SizedBox(height: 12),
                  const Text(
                    '로딩 실패',
                    style: TextStyle(color: AppColors.textSecondary),
                  ),
                  const SizedBox(height: 8),
                  OutlinedButton(
                    onPressed: () => ref.invalidate(favoritesProvider),
                    child: const Text('다시 시도'),
                  ),
                ],
              ),
            ),
          ),

          // 삭제 중 로딩 오버레이
          if (removeState.isLoading)
            const Positioned.fill(
              child: ColoredBox(
                color: Colors.black45,
                child: Center(
                  child: CircularProgressIndicator(color: AppColors.accent),
                ),
              ),
            ),
        ],
      ),
    );
  }
}

class _EmptyState extends StatelessWidget {
  @override
  Widget build(BuildContext context) {
    return Center(
      child: Column(
        mainAxisSize: MainAxisSize.min,
        children: [
          Container(
            width: 80,
            height: 80,
            decoration: BoxDecoration(
              shape: BoxShape.circle,
              color: AppColors.accent.withOpacity(0.08),
            ),
            child: const Icon(
              Icons.bookmark_outline_rounded,
              size: 40,
              color: AppColors.textTertiary,
            ),
          ),
          const SizedBox(height: 20),
          const Text(
            '저장된 기사가 없습니다',
            style: TextStyle(
              fontSize: 16,
              fontWeight: FontWeight.w600,
              color: AppColors.textSecondary,
            ),
          ),
          const SizedBox(height: 8),
          const Text(
            '기사 상세 화면에서 북마크를 눌러\n즐겨찾기에 추가하세요',
            textAlign: TextAlign.center,
            style: TextStyle(
              fontSize: 13,
              color: AppColors.textTertiary,
              height: 1.5,
            ),
          ),
        ],
      ),
    );
  }
}

class _FavoriteItem extends StatelessWidget {
  final Map<String, dynamic> item;
  final VoidCallback onDelete;
  final VoidCallback onTap;

  const _FavoriteItem({
    required this.item,
    required this.onDelete,
    required this.onTap,
  });

  @override
  Widget build(BuildContext context) {
    final title = item['title'] as String? ?? '제목 없음';
    final source = item['source'] as String? ?? '';
    final category = item['category'] as String?;
    final savedAtRaw = item['saved_at'] as String? ?? item['created_at'] as String?;
    String savedAtLabel = '';
    if (savedAtRaw != null) {
      try {
        final dt = DateTime.parse(savedAtRaw).toLocal();
        savedAtLabel = DateFormat('yyyy.MM.dd', 'ko_KR').format(dt);
      } catch (_) {}
    }

    return GestureDetector(
      onTap: onTap,
      child: Container(
        margin: const EdgeInsets.only(bottom: 10),
        padding: const EdgeInsets.all(14),
        decoration: BoxDecoration(
          color: AppColors.surfaceCard,
          borderRadius: BorderRadius.circular(14),
          border: Border.all(color: AppColors.surfaceLight),
        ),
        child: Row(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            // 즐겨찾기 아이콘
            Container(
              width: 36,
              height: 36,
              decoration: BoxDecoration(
                color: AppColors.accent.withOpacity(0.08),
                borderRadius: BorderRadius.circular(10),
              ),
              child: const Icon(
                Icons.bookmark_rounded,
                size: 18,
                color: AppColors.accent,
              ),
            ),
            const SizedBox(width: 12),

            // 콘텐츠
            Expanded(
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  if (category != null)
                    Padding(
                      padding: const EdgeInsets.only(bottom: 4),
                      child: Text(
                        _categoryLabel(category),
                        style: TextStyle(
                          fontSize: 11,
                          fontWeight: FontWeight.w600,
                          color: AppColors.categoryColor(category),
                        ),
                      ),
                    ),
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
                  const SizedBox(height: 6),
                  Row(
                    children: [
                      if (source.isNotEmpty) ...[
                        Text(
                          source,
                          style: const TextStyle(
                            fontSize: 11,
                            color: AppColors.textTertiary,
                          ),
                        ),
                        const SizedBox(width: 8),
                        Container(
                          width: 2,
                          height: 2,
                          decoration: const BoxDecoration(
                            shape: BoxShape.circle,
                            color: AppColors.textTertiary,
                          ),
                        ),
                        const SizedBox(width: 8),
                      ],
                      if (savedAtLabel.isNotEmpty)
                        Text(
                          savedAtLabel,
                          style: const TextStyle(
                            fontSize: 11,
                            color: AppColors.textTertiary,
                          ),
                        ),
                    ],
                  ),
                ],
              ),
            ),

            // 삭제 버튼
            GestureDetector(
              onTap: () => _confirmDelete(context),
              behavior: HitTestBehavior.opaque,
              child: Padding(
                padding: const EdgeInsets.only(left: 8),
                child: Icon(
                  Icons.close_rounded,
                  size: 18,
                  color: AppColors.textTertiary,
                ),
              ),
            ),
          ],
        ),
      ),
    );
  }

  void _confirmDelete(BuildContext context) {
    showDialog<bool>(
      context: context,
      builder: (ctx) => AlertDialog(
        backgroundColor: AppColors.surfaceCard,
        shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(16)),
        title: const Text(
          '즐겨찾기 삭제',
          style: TextStyle(color: AppColors.textPrimary, fontSize: 17),
        ),
        content: const Text(
          '이 기사를 즐겨찾기에서 삭제하시겠습니까?',
          style: TextStyle(color: AppColors.textSecondary, fontSize: 14),
        ),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(ctx, false),
            child: const Text(
              '취소',
              style: TextStyle(color: AppColors.textTertiary),
            ),
          ),
          TextButton(
            onPressed: () {
              Navigator.pop(ctx, true);
              onDelete();
            },
            child: const Text(
              '삭제',
              style: TextStyle(color: AppColors.error),
            ),
          ),
        ],
      ),
    );
  }

  String _categoryLabel(String category) {
    const labels = {
      'politics': '정치',
      'economy': '경제',
      'society': '사회',
      'world': '국제',
      'tech': 'IT/기술',
      'science': '과학',
      'culture': '문화',
      'sports': '스포츠',
      'entertainment': '연예',
      'lifestyle': '생활',
    };
    return labels[category] ?? category;
  }
}
