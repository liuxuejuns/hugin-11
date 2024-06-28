from django.urls import path

from testrecord.views import *


urlpatterns = [
    path('buildtest/', BuildTest.as_view(), name='buildtest'),
    # path('starttest/', StartTest.as_view(), name='starttest'),
    path('nextstage/', NextStage.as_view(), name='nextstage'),
    path('starttestitem/', StartTestItem.as_view(), name='starttestitem'),
    path('endtestitem/', EndTestItem.as_view(), name='endtestitem'),
    path('gettestitemrecord/', GetTestItemRecord.as_view(), name='gettestitemrecord'),
    path('modifyip/', ModifyIP.as_view(), name='modifyip'),
]
