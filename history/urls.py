from django.urls import path

from history.views import *


urlpatterns = [
    path(
        'gettestitemrecordhistory/',
        GetTestItemRecordHistory.as_view(),
        name='gettestitemrecordhistory',
    ),
    path(
        'getrackhistory/',
        GetRackHistory.as_view(),
        name='getrackhistory',
    ),
]
