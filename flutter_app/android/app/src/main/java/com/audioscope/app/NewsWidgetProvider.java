package com.audioscope.app;

import android.app.PendingIntent;
import android.appwidget.AppWidgetManager;
import android.appwidget.AppWidgetProvider;
import android.content.Context;
import android.content.Intent;
import android.widget.RemoteViews;

/**
 * AudioScope 홈 화면 위젯.
 * 메인 뉴스 헤드라인을 표시하고 탭하면 앱이 열립니다.
 *
 * Flutter home_widget 패키지와 연동하여 데이터를 SharedPreferences에서 읽습니다.
 * 실제 구현 시 home_widget 패키지를 pubspec.yaml에 추가하고
 * Flutter 측에서 HomeWidget.updateWidget()을 호출합니다.
 */
public class NewsWidgetProvider extends AppWidgetProvider {

    @Override
    public void onUpdate(Context context, AppWidgetManager appWidgetManager, int[] appWidgetIds) {
        for (int appWidgetId : appWidgetIds) {
            updateAppWidget(context, appWidgetManager, appWidgetId);
        }
    }

    static void updateAppWidget(Context context, AppWidgetManager appWidgetManager, int appWidgetId) {
        RemoteViews views = new RemoteViews(context.getPackageName(), R.layout.news_widget_layout);

        // 위젯 클릭 시 앱 열기
        Intent launchIntent = context.getPackageManager().getLaunchIntentForPackage(context.getPackageName());
        if (launchIntent != null) {
            PendingIntent pendingIntent = PendingIntent.getActivity(
                context, 0, launchIntent,
                PendingIntent.FLAG_UPDATE_CURRENT | PendingIntent.FLAG_IMMUTABLE
            );
            views.setOnClickPendingIntent(R.id.widget_root, pendingIntent);
            views.setOnClickPendingIntent(R.id.widget_open_app, pendingIntent);
        }

        appWidgetManager.updateAppWidget(appWidgetId, views);
    }

    @Override
    public void onEnabled(Context context) {
        // 첫 위젯 추가 시
    }

    @Override
    public void onDisabled(Context context) {
        // 마지막 위젯 제거 시
    }
}
