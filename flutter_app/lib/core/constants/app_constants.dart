/// 앱 전역 상수.
class AppConstants {
  AppConstants._();

  static const appName = 'AudioScope';
  static const appTagline = '5분 안에 귀에 꽂아드리는 전 세계 주요 시사';
  static const appDescription = '세상을 AI 아나운서와 함께, 귀로 살피는 세계';

  // API
  static const apiBaseUrl = 'https://your-api-domain.com';
  static const tokenKey = 'access_token';
  static const refreshTokenKey = 'refresh_token';

  // Briefing periods
  static const periods = ['morning', 'lunch', 'evening'];
  static const periodLabels = {
    'morning': '아침 브리핑',
    'lunch': '점심 브리핑',
    'evening': '저녁 브리핑',
  };
  static const periodEmojis = {
    'morning': '🌅',
    'lunch': '☀️',
    'evening': '🌙',
  };
  static const periodTimes = {
    'morning': '06:00',
    'lunch': '12:00',
    'evening': '18:00',
  };

  // Categories
  static const categoryLabels = {
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

  // Subscription
  static const freePeriod = 'morning';
  static const premiumMonthlyKRW = 4900;
  static const premiumYearlyKRW = 39000;
  static const trialDays = 7;

  // Onboarding
  static const onboardingPages = [
    {
      'title': '세상의 소리를 담다',
      'subtitle': 'AI 아나운서가 매일 3회\n전 세계 뉴스를 읽어드립니다',
      'icon': 'headphones',
    },
    {
      'title': '5분이면 충분합니다',
      'subtitle': '바쁜 아침, 출퇴근길에\n귀로 세상을 살피세요',
      'icon': 'timer',
    },
    {
      'title': '당신만의 뉴스룸',
      'subtitle': '관심 카테고리를 선택하면\n맞춤 브리핑을 제공합니다',
      'icon': 'tune',
    },
  ];
}
