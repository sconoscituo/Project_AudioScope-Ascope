import 'package:flutter/material.dart';

import '../../core/theme/app_theme.dart';
import 'legal_widgets.dart';

class PrivacyScreen extends StatelessWidget {
  const PrivacyScreen({super.key});

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: AppColors.primary,
      appBar: AppBar(
        title: const Text('개인정보 처리방침'),
        backgroundColor: AppColors.primary,
      ),
      body: const SingleChildScrollView(
        padding: EdgeInsets.symmetric(horizontal: 20, vertical: 16),
        child: _PrivacyContent(),
      ),
    );
  }
}

class _PrivacyContent extends StatelessWidget {
  const _PrivacyContent();

  @override
  Widget build(BuildContext context) {
    return const Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        LegalHeader(
          title: 'AudioScope 개인정보 처리방침',
          effectiveDate: '시행일: 2025년 1월 1일',
        ),
        _InfoBox(
          text:
              'AudioScope는 이용자의 개인정보를 소중히 여깁니다. '
              '본 방침은 수집하는 정보, 사용 방식, 보호 방법을 명확하게 안내합니다.',
        ),
        LegalSection(
          title: '제1조 (수집하는 개인정보 항목)',
          body:
              '① 회원가입 시 수집 항목\n'
              '   • 필수: 이름, 이메일 주소, 소셜 계정 식별자(Google/Apple)\n'
              '   • 선택: 프로필 사진\n\n'
              '② 서비스 이용 과정에서 자동 수집\n'
              '   • 청취 이력, 관심 카테고리, 앱 사용 패턴\n'
              '   • 기기 정보(OS, 앱 버전), 접속 로그\n\n'
              '③ 유료 결제 시\n'
              '   • 결제 처리는 Google Play / App Store를 통해 이루어지며, '
              '   회사는 카드번호 등 민감한 결제 정보를 직접 수집·저장하지 않습니다.',
        ),
        LegalSection(
          title: '제2조 (개인정보의 수집 및 이용 목적)',
          body:
              '① 서비스 제공: 맞춤형 뉴스 브리핑 생성, 청취 이력 관리\n'
              '② 회원 관리: 본인 확인, 부정 이용 방지, 고지사항 전달\n'
              '③ 서비스 개선: 이용 패턴 분석을 통한 콘텐츠 품질 향상\n'
              '④ 마케팅: 이용자가 별도 동의한 경우에 한해 프로모션 안내 발송',
        ),
        LegalSection(
          title: '제3조 (개인정보 보유 및 이용 기간)',
          body:
              '① 회원 탈퇴 시 즉시 파기합니다. 단, 관계 법령에 의해 보존이 필요한 경우 아래 기간 동안 보관합니다.\n\n'
              '   • 계약 또는 청약 철회 기록: 5년 (전자상거래 등에서의 소비자 보호에 관한 법률)\n'
              '   • 소비자 불만 또는 분쟁 처리 기록: 3년\n'
              '   • 접속 로그: 3개월 (통신비밀보호법)\n\n'
              '② 동의 철회(회원 탈퇴) 시까지 보유합니다.',
        ),
        LegalSection(
          title: '제4조 (개인정보의 제3자 제공)',
          body:
              '회사는 이용자의 개인정보를 원칙적으로 외부에 제공하지 않습니다. '
              '다만, 아래의 경우는 예외로 합니다.\n\n'
              '① 이용자가 사전에 동의한 경우\n'
              '② 법령의 규정에 의거하거나 수사기관의 적법한 요청이 있는 경우',
        ),
        LegalSection(
          title: '제5조 (개인정보 처리 위탁)',
          body:
              '서비스 운영을 위해 아래와 같이 개인정보 처리를 위탁하고 있습니다.\n\n'
              '   • Firebase (Google LLC): 인증, 푸시 알림\n'
              '   • AWS / GCP: 서버 인프라 및 데이터 저장\n'
              '   • OpenAI: 뉴스 요약 AI 처리 (원문 기사만 전달, 개인정보 미포함)\n\n'
              '위탁 업체는 위탁 업무 수행 목적 외 개인정보를 이용하지 않습니다.',
        ),
        LegalSection(
          title: '제6조 (이용자의 권리)',
          body:
              '이용자는 언제든지 아래 권리를 행사할 수 있습니다.\n\n'
              '① 개인정보 열람 요청\n'
              '② 오류가 있는 경우 정정 요청\n'
              '③ 삭제 요청 (단, 법령에 따른 보존 의무가 있는 경우 제외)\n'
              '④ 처리 정지 요청\n\n'
              '권리 행사는 설정 → 문의하기 또는 support@audioscope.io 로 연락해 주세요. '
              '요청 후 10일 이내에 처리합니다.',
        ),
        LegalSection(
          title: '제7조 (개인정보 보호 조치)',
          body:
              '회사는 개인정보 보호를 위해 다음과 같은 기술적·관리적 조치를 취합니다.\n\n'
              '① 전송 구간 SSL/TLS 암호화\n'
              '② 비밀번호 및 민감 정보 암호화 저장\n'
              '③ 개인정보 접근 권한 최소화 및 접근 로그 관리\n'
              '④ 정기적인 보안 점검 및 임직원 교육',
        ),
        LegalSection(
          title: '제8조 (개인정보 보호책임자)',
          body:
              '개인정보 관련 문의, 불만, 피해 구제 등에 관한 사항은 아래 담당자에게 연락해 주세요.\n\n'
              '   • 이메일: privacy@audioscope.io\n'
              '   • 처리 시간: 영업일 기준 3일 이내',
        ),
        LegalSection(
          title: '제9조 (방침 변경)',
          body:
              '이 개인정보 처리방침은 법령, 정책 또는 보안 기술의 변경에 따라 업데이트될 수 있습니다. '
              '변경 시 앱 내 공지사항을 통해 최소 7일 전에 안내합니다.',
        ),
        SizedBox(height: 40),
        Center(
          child: Text(
            '문의: privacy@audioscope.io',
            style: TextStyle(fontSize: 12, color: AppColors.textTertiary),
          ),
        ),
        SizedBox(height: 24),
      ],
    );
  }
}

class _InfoBox extends StatelessWidget {
  final String text;
  const _InfoBox({required this.text});

  @override
  Widget build(BuildContext context) {
    return Container(
      margin: const EdgeInsets.only(bottom: 24),
      padding: const EdgeInsets.all(14),
      decoration: BoxDecoration(
        color: AppColors.accent.withOpacity(0.08),
        borderRadius: BorderRadius.circular(12),
        border: Border.all(color: AppColors.accent.withOpacity(0.2)),
      ),
      child: const Row(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Icon(Icons.info_outline_rounded, color: AppColors.accent, size: 18),
          SizedBox(width: 10),
          Expanded(
            child: Text(
              'AudioScope는 이용자의 개인정보를 소중히 여깁니다. '
              '본 방침은 수집하는 정보, 사용 방식, 보호 방법을 명확하게 안내합니다.',
              style: TextStyle(
                fontSize: 13,
                color: AppColors.textSecondary,
                height: 1.6,
              ),
            ),
          ),
        ],
      ),
    );
  }
}
