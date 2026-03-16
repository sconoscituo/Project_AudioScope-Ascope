import 'package:flutter/material.dart';

import '../../core/theme/app_theme.dart';

class FaqScreen extends StatelessWidget {
  const FaqScreen({super.key});

  static const _items = [
    _FaqItem(
      question: 'AudioScope가 무엇인가요?',
      answer:
          'AudioScope는 매일 주요 뉴스를 AI가 요약하고 음성으로 전달해주는 오디오 브리핑 앱입니다. '
          '출퇴근길, 운동 중 등 눈을 쓸 수 없는 상황에서도 뉴스를 들을 수 있습니다.',
    ),
    _FaqItem(
      question: '브리핑은 하루에 몇 번 제공되나요?',
      answer:
          '아침(06:00), 점심(12:00), 저녁(18:00) 하루 3회 제공됩니다.\n'
          '무료 플랜은 아침 브리핑 1회, 광고 시청 시 추가 1회가 제공됩니다. '
          'Premium 플랜은 모든 브리핑을 무제한으로 이용할 수 있습니다.',
    ),
    _FaqItem(
      question: '무료 플랜과 Premium의 차이는 무엇인가요?',
      answer:
          '무료 플랜: 아침 브리핑 1회/일, 광고 시청 시 +1회 추가\n\n'
          'Premium 플랜: 아침·점심·저녁 브리핑 무제한, 광고 없음, '
          '프리미엄 음성 품질, 트렌드 키워드 심층 분석 제공',
    ),
    _FaqItem(
      question: '관심 카테고리는 어떻게 바꾸나요?',
      answer:
          '설정 → 뉴스 카테고리에서 언제든지 변경할 수 있습니다. '
          '정치, 경제, 세계, IT/기술, 사회, 과학 중 원하는 항목을 선택하세요. '
          '변경 사항은 다음 브리핑 생성 시 반영됩니다.',
    ),
    _FaqItem(
      question: '브리핑 음성이 자연스럽지 않아요.',
      answer:
          'AI 음성 합성(TTS) 기술을 사용하기 때문에 일부 고유명사나 전문 용어에서 '
          '어색하게 들릴 수 있습니다. Premium 플랜에서는 더 자연스러운 고품질 음성이 제공됩니다. '
          '지속적으로 품질을 개선하고 있습니다.',
    ),
    _FaqItem(
      question: '브리핑을 오프라인에서도 들을 수 있나요?',
      answer:
          '현재 버전에서는 오프라인 재생을 지원하지 않습니다. '
          '브리핑 재생 시 인터넷 연결이 필요합니다. '
          '오프라인 다운로드 기능은 추후 업데이트에서 제공될 예정입니다.',
    ),
    _FaqItem(
      question: 'Premium 구독은 어떻게 취소하나요?',
      answer:
          '설정 → 구독 관리 화면에서 구독을 취소할 수 있습니다. '
          '취소 후에도 현재 구독 기간이 끝날 때까지 Premium 혜택이 유지됩니다. '
          '환불은 각 앱스토어(App Store / Google Play) 정책에 따라 처리됩니다.',
    ),
    _FaqItem(
      question: '추천인 코드는 어떤 혜택이 있나요?',
      answer:
          '추천인 코드를 입력하면 추천한 분과 입력한 분 모두에게 Premium 체험 기간이 제공됩니다. '
          '내 추천 코드는 설정 → 프로필 화면에서 확인할 수 있습니다.',
    ),
    _FaqItem(
      question: '계정 정보는 어떻게 변경하나요?',
      answer:
          '현재 이름과 프로필 사진은 Google 또는 Apple 계정 정보와 연동됩니다. '
          '변경을 원하신다면 연동된 소셜 계정에서 수정 후 앱을 재로그인하세요.',
    ),
    _FaqItem(
      question: '앱에 문제가 생겼어요. 어떻게 문의하나요?',
      answer:
          '설정 → 문의하기를 통해 불편사항을 남겨주세요. '
          '영업일 기준 1~2일 내에 이메일로 답변 드립니다. '
          '긴급 문의는 support@audioscope.io 로 연락해주세요.',
    ),
  ];

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: AppColors.primary,
      appBar: AppBar(
        title: const Text('자주 묻는 질문'),
        backgroundColor: AppColors.primary,
      ),
      body: ListView.separated(
        padding: const EdgeInsets.symmetric(horizontal: 20, vertical: 16),
        itemCount: _items.length,
        separatorBuilder: (_, __) => const SizedBox(height: 8),
        itemBuilder: (context, index) => _FaqTile(item: _items[index]),
      ),
    );
  }
}

class _FaqItem {
  final String question;
  final String answer;
  const _FaqItem({required this.question, required this.answer});
}

class _FaqTile extends StatefulWidget {
  final _FaqItem item;
  const _FaqTile({required this.item});

  @override
  State<_FaqTile> createState() => _FaqTileState();
}

class _FaqTileState extends State<_FaqTile> {
  bool _expanded = false;

  @override
  Widget build(BuildContext context) {
    return AnimatedContainer(
      duration: const Duration(milliseconds: 200),
      decoration: BoxDecoration(
        color: AppColors.surfaceCard,
        borderRadius: BorderRadius.circular(14),
        border: _expanded
            ? Border.all(color: AppColors.accent.withOpacity(0.3), width: 1)
            : null,
      ),
      child: Material(
        color: Colors.transparent,
        child: InkWell(
          borderRadius: BorderRadius.circular(14),
          onTap: () => setState(() => _expanded = !_expanded),
          child: Padding(
            padding: const EdgeInsets.all(16),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Row(
                  children: [
                    Text(
                      'Q',
                      style: TextStyle(
                        fontSize: 14,
                        fontWeight: FontWeight.w700,
                        color: AppColors.accent,
                      ),
                    ),
                    const SizedBox(width: 10),
                    Expanded(
                      child: Text(
                        widget.item.question,
                        style: const TextStyle(
                          fontSize: 14,
                          fontWeight: FontWeight.w600,
                          color: AppColors.textPrimary,
                          height: 1.4,
                        ),
                      ),
                    ),
                    const SizedBox(width: 8),
                    Icon(
                      _expanded
                          ? Icons.keyboard_arrow_up_rounded
                          : Icons.keyboard_arrow_down_rounded,
                      color: AppColors.textTertiary,
                      size: 20,
                    ),
                  ],
                ),
                if (_expanded) ...[
                  const SizedBox(height: 12),
                  const Divider(color: AppColors.surfaceLight, height: 1),
                  const SizedBox(height: 12),
                  Row(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      const Text(
                        'A',
                        style: TextStyle(
                          fontSize: 14,
                          fontWeight: FontWeight.w700,
                          color: AppColors.success,
                        ),
                      ),
                      const SizedBox(width: 10),
                      Expanded(
                        child: Text(
                          widget.item.answer,
                          style: const TextStyle(
                            fontSize: 13,
                            color: AppColors.textSecondary,
                            height: 1.6,
                          ),
                        ),
                      ),
                    ],
                  ),
                ],
              ],
            ),
          ),
        ),
      ),
    );
  }
}
