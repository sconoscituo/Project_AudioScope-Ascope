import 'package:flutter/material.dart';

import '../../core/theme/app_theme.dart';
import 'legal_widgets.dart';

class TermsScreen extends StatelessWidget {
  const TermsScreen({super.key});

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: AppColors.primary,
      appBar: AppBar(
        title: const Text('이용약관'),
        backgroundColor: AppColors.primary,
      ),
      body: const SingleChildScrollView(
        padding: EdgeInsets.symmetric(horizontal: 20, vertical: 16),
        child: _TermsContent(),
      ),
    );
  }
}

class _TermsContent extends StatelessWidget {
  const _TermsContent();

  @override
  Widget build(BuildContext context) {
    return const Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        LegalHeader(
          title: 'AudioScope 서비스 이용약관',
          effectiveDate: '시행일: 2025년 1월 1일',
        ),
        LegalSection(
          title: '제1조 (목적)',
          body:
              '이 약관은 AudioScope(이하 "회사")가 제공하는 AI 오디오 뉴스 브리핑 서비스(이하 "서비스")의 이용에 관한 '
              '회사와 이용자 간의 권리·의무 및 책임 사항, 기타 필요한 사항을 규정함을 목적으로 합니다.',
        ),
        LegalSection(
          title: '제2조 (정의)',
          body:
              '① "서비스"란 회사가 제공하는 AI 기반 뉴스 요약 및 음성 브리핑 애플리케이션과 관련 제반 서비스를 의미합니다.\n\n'
              '② "이용자"란 이 약관에 따라 회사가 제공하는 서비스를 받는 회원 및 비회원을 말합니다.\n\n'
              '③ "회원"이란 회사에 개인정보를 제공하여 회원등록을 한 자로서, 회사의 정보를 지속적으로 제공받으며 서비스를 이용할 수 있는 자를 말합니다.\n\n'
              '④ "유료 서비스(Premium)"란 회사가 유료로 제공하는 구독형 서비스를 말합니다.',
        ),
        LegalSection(
          title: '제3조 (약관의 효력 및 변경)',
          body:
              '① 이 약관은 서비스 화면에 게시하거나 기타의 방법으로 이용자에게 공지함으로써 효력이 발생합니다.\n\n'
              '② 회사는 합리적인 사유가 발생할 경우 관련 법령에 위배되지 않는 범위 내에서 이 약관을 변경할 수 있으며, '
              '변경된 약관은 서비스 내 공지사항을 통해 최소 7일 전에 공지합니다.\n\n'
              '③ 이용자는 변경된 약관에 동의하지 않을 경우 서비스 이용을 중단하고 탈퇴할 수 있습니다.',
        ),
        LegalSection(
          title: '제4조 (서비스의 제공 및 변경)',
          body:
              '① 회사는 다음과 같은 서비스를 제공합니다.\n'
              '   • AI 기반 뉴스 요약 및 오디오 브리핑 생성\n'
              '   • 카테고리별 맞춤 뉴스 큐레이션\n'
              '   • 트렌드 키워드 분석\n'
              '   • 구독 플랜에 따른 추가 서비스\n\n'
              '② 회사는 서비스의 내용, 품질 향상을 위해 서비스를 변경할 수 있으며, '
              '중요한 변경의 경우 사전에 공지합니다.',
        ),
        LegalSection(
          title: '제5조 (서비스 이용 제한)',
          body:
              '이용자는 다음 행위를 하여서는 안 됩니다.\n\n'
              '① 타인의 계정을 도용하거나 허위 정보로 가입하는 행위\n'
              '② 서비스를 통해 제공되는 콘텐츠를 무단으로 복제·배포·상업적으로 이용하는 행위\n'
              '③ 서비스의 정상적인 운영을 방해하는 행위\n'
              '④ 관련 법령을 위반하는 행위',
        ),
        LegalSection(
          title: '제6조 (유료 서비스 및 환불)',
          body:
              '① 유료 서비스(Premium) 이용 요금 및 결제 방법은 서비스 내 구독 화면에서 확인할 수 있습니다.\n\n'
              '② 구독은 이용자가 직접 해지하지 않는 한 자동 갱신됩니다.\n\n'
              '③ 환불은 Google Play 또는 App Store의 환불 정책에 따릅니다. '
              '앱 내 결제 관련 문의는 각 플랫폼 고객센터를 통해 진행해 주시기 바랍니다.',
        ),
        LegalSection(
          title: '제7조 (책임의 한계)',
          body:
              '① 회사는 천재지변, 전쟁, 기간통신사업자의 서비스 중지 등 불가항력적 사유로 인한 서비스 제공 불능에 대해 책임을 지지 않습니다.\n\n'
              '② AI가 생성하는 브리핑 내용은 원본 뉴스 기사를 기반으로 하나, '
              '요약 과정에서 원문과 차이가 발생할 수 있습니다. '
              '중요한 의사결정에는 반드시 원문 기사를 확인하시기 바랍니다.',
        ),
        LegalSection(
          title: '제8조 (준거법 및 관할법원)',
          body:
              '이 약관은 대한민국 법률에 따라 해석되며, '
              '서비스 이용으로 발생한 분쟁에 대해서는 대한민국 법원을 관할 법원으로 합니다.',
        ),
        SizedBox(height: 40),
        Center(
          child: Text(
            '문의: support@audioscope.io',
            style: TextStyle(fontSize: 12, color: AppColors.textTertiary),
          ),
        ),
        SizedBox(height: 24),
      ],
    );
  }
}
