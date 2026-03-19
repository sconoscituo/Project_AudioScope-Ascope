import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import '../../core/api/api_client.dart';
import '../../core/providers/providers.dart';
import '../../core/theme/app_theme.dart';

/// 설정 화면에서 진입하는 관심 카테고리 설정 화면.
/// 체크박스 리스트 + 저장 버튼으로 구성됩니다.
class CategorySettingsScreen extends ConsumerStatefulWidget {
  const CategorySettingsScreen({super.key});

  @override
  ConsumerState<CategorySettingsScreen> createState() =>
      _CategorySettingsScreenState();
}

class _CategorySettingsScreenState
    extends ConsumerState<CategorySettingsScreen> {
  // 백엔드 NEWS_CATEGORIES와 동일한 순서
  static const Map<String, String> _categoryLabels = {
    'politics': '정치',
    'economy': '경제',
    'society': '사회',
    'world': '세계',
    'tech': 'IT/기술',
    'science': '과학',
    'culture': '문화',
    'sports': '스포츠',
    'entertainment': '연예',
    'lifestyle': '생활',
  };

  final Set<String> _selected = {};
  bool _loading = true;
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
      final cats =
          (data?['categories'] as List<dynamic>?)?.cast<String>() ?? [];
      if (mounted) {
        setState(() {
          _selected.addAll(cats);
          _loading = false;
        });
      }
    } catch (_) {
      if (mounted) setState(() => _loading = false);
    }
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
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(content: Text('저장되었습니다')),
        );
        context.pop();
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
        title: const Text('관심 카테고리 설정'),
        leading: IconButton(
          icon: const Icon(Icons.arrow_back_ios_new_rounded, size: 20),
          onPressed: () => context.pop(),
        ),
      ),
      body: _loading
          ? const Center(
              child: CircularProgressIndicator(color: AppColors.accent),
            )
          : Column(
              children: [
                Expanded(
                  child: ListView(
                    children: _categoryLabels.entries.map((entry) {
                      final isSelected = _selected.contains(entry.key);
                      return CheckboxListTile(
                        value: isSelected,
                        onChanged: (checked) {
                          setState(() {
                            if (checked == true) {
                              _selected.add(entry.key);
                            } else {
                              _selected.remove(entry.key);
                            }
                          });
                        },
                        title: Text(
                          entry.value,
                          style: const TextStyle(
                            fontSize: 15,
                            color: AppColors.textPrimary,
                          ),
                        ),
                        activeColor: AppColors.accent,
                        checkColor: Colors.white,
                        side: const BorderSide(color: AppColors.textTertiary),
                        contentPadding: const EdgeInsets.symmetric(
                          horizontal: 20,
                          vertical: 2,
                        ),
                      );
                    }).toList(),
                  ),
                ),
                Padding(
                  padding: const EdgeInsets.fromLTRB(20, 8, 20, 24),
                  child: SizedBox(
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
                          : const Text('저장'),
                    ),
                  ),
                ),
              ],
            ),
    );
  }
}
