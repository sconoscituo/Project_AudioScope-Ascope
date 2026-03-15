import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import '../../core/api/api_client.dart';
import '../../core/constants/app_constants.dart';
import '../../core/providers/providers.dart';
import '../../core/theme/app_theme.dart';

/// 뉴스 카테고리 선택 화면.
class CategoryScreen extends ConsumerStatefulWidget {
  final bool isInitialSetup;
  const CategoryScreen({super.key, this.isInitialSetup = false});

  @override
  ConsumerState<CategoryScreen> createState() => _CategoryScreenState();
}

class _CategoryScreenState extends ConsumerState<CategoryScreen> {
  final Set<String> _selected = {};
  bool _saving = false;

  @override
  void initState() {
    super.initState();
    _loadCurrent();
  }

  Future<void> _loadCurrent() async {
    try {
      final response = await ApiClient().get<Map<String, dynamic>>(
        '/api/v1/users/me/categories',
      );
      final data = ApiClient.extractData<Map<String, dynamic>>(response);
      final cats = (data?['categories'] as List<dynamic>?)?.cast<String>() ?? [];
      if (mounted) setState(() => _selected.addAll(cats));
    } catch (_) {}
  }

  Future<void> _save() async {
    if (_selected.isEmpty) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('최소 1개 카테고리를 선택해주세요')),
      );
      return;
    }

    setState(() => _saving = true);
    try {
      await ApiClient().put('/api/v1/users/me/categories', data: {
        'categories': _selected.toList(),
      });
      ref.invalidate(categoriesProvider);
      if (mounted) {
        if (widget.isInitialSetup) {
          context.go('/home');
        } else {
          context.pop();
        }
      }
    } catch (_) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(content: Text('저장 실패. 다시 시도해주세요.')),
        );
      }
    } finally {
      if (mounted) setState(() => _saving = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: AppColors.primary,
      appBar: AppBar(
        title: const Text('뉴스 카테고리'),
        leading: widget.isInitialSetup
            ? null
            : IconButton(
                icon: const Icon(Icons.arrow_back_ios_new_rounded, size: 20),
                onPressed: () => context.pop(),
              ),
      ),
      body: SafeArea(
        child: Padding(
          padding: const EdgeInsets.all(20),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              if (widget.isInitialSetup) ...[
                const Text(
                  '관심 있는 뉴스를\n선택해주세요',
                  style: TextStyle(
                    fontSize: 24,
                    fontWeight: FontWeight.w700,
                    color: AppColors.textPrimary,
                    height: 1.3,
                  ),
                ),
                const SizedBox(height: 8),
                const Text(
                  '선택한 카테고리로 맞춤 브리핑을 제공합니다',
                  style: TextStyle(fontSize: 14, color: AppColors.textSecondary),
                ),
                const SizedBox(height: 28),
              ],

              Expanded(
                child: Wrap(
                  spacing: 10,
                  runSpacing: 10,
                  children: AppConstants.categoryLabels.entries.map((entry) {
                    final isSelected = _selected.contains(entry.key);
                    final color = AppColors.categoryColor(entry.key);
                    return GestureDetector(
                      onTap: () {
                        setState(() {
                          if (isSelected) {
                            _selected.remove(entry.key);
                          } else {
                            _selected.add(entry.key);
                          }
                        });
                      },
                      child: AnimatedContainer(
                        duration: const Duration(milliseconds: 200),
                        padding: const EdgeInsets.symmetric(
                          horizontal: 20,
                          vertical: 14,
                        ),
                        decoration: BoxDecoration(
                          color: isSelected
                              ? color.withOpacity(0.15)
                              : AppColors.surfaceCard,
                          borderRadius: BorderRadius.circular(14),
                          border: Border.all(
                            color: isSelected
                                ? color.withOpacity(0.5)
                                : AppColors.surfaceLight,
                            width: isSelected ? 2 : 1,
                          ),
                        ),
                        child: Row(
                          mainAxisSize: MainAxisSize.min,
                          children: [
                            if (isSelected) ...[
                              Icon(Icons.check_circle_rounded,
                                  size: 18, color: color),
                              const SizedBox(width: 6),
                            ],
                            Text(
                              entry.value,
                              style: TextStyle(
                                fontSize: 15,
                                fontWeight:
                                    isSelected ? FontWeight.w600 : FontWeight.w400,
                                color: isSelected
                                    ? color
                                    : AppColors.textSecondary,
                              ),
                            ),
                          ],
                        ),
                      ),
                    );
                  }).toList(),
                ),
              ),

              // 선택 상태 + 저장
              Text(
                '${_selected.length}개 선택됨',
                style: const TextStyle(
                  fontSize: 14,
                  color: AppColors.textTertiary,
                ),
              ),
              const SizedBox(height: 12),
              SizedBox(
                width: double.infinity,
                height: 54,
                child: ElevatedButton(
                  onPressed: _saving ? null : _save,
                  child: _saving
                      ? const SizedBox(
                          width: 20,
                          height: 20,
                          child: CircularProgressIndicator(
                            strokeWidth: 2,
                            color: Colors.white,
                          ),
                        )
                      : Text(widget.isInitialSetup ? '시작하기' : '저장'),
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }
}
