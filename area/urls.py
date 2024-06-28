from django.urls import path

from area.views import AreaList,CreateArea,AreaInfo

urlpatterns = [
    path('arealist/',AreaList.as_view(),name='area_list'),
    path('createarea/',CreateArea.as_view(),name='create_area'),
    path('info/<int:id>/',AreaInfo.as_view(),name='area_info'),
]