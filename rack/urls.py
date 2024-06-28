from django.urls import path

from rack import views


urlpatterns = [
    path('racklist/', views.RackList.as_view(), name='rack_list'),
    path('rackdetail/<int:id>/', views.RackDetail.as_view(), name='rack_detail'),
    path(
        'rackcomponent/<int:rack_id>/',
        views.RackComponentList.as_view(),
        name='rack_component_list',
    ),
    path(
        'rackcomponentnode/<int:rack_node_id>/',
        views.RackComponentNodeList.as_view(),
        name='rack_component_node_list',
    ),
    path(
        'rackcomponentassembly/',
        views.RackComponentAssembly.as_view(),
        name='rack_component_assembly',
    ),
    path(
        'rackcomponentdeleave/<int:id>/',
        views.RackComponentDeleave.as_view(),
        name='rack_component_deleave',
    ),
    path(
        'racklocationlist/<int:area_id>/',
        views.RackLocationList.as_view(),
        name='rack_location_list',
    ),
    # path(
    #     'createracklocation/<int:area_id>/',
    #     views.CreateRackLocation.as_view(),
    #     name='create_rack_location',
    # ),
    path(
        'racklocation/<int:area_id>/<int:id>/',
        views.RackLocationView.as_view(),
        name='rack_location',
    ),
    path(
        'racklocationcheckin/',
        views.RackLocationCheckin.as_view(),
        name='rack_location_checkin',
    ),
    path('scanin/', views.ScanIn.as_view(), name='scan_in'),
    path(
        'scanindeleave/<int:id>/<int:racknodeid>/', views.ScanInDeleave.as_view(), name='scan_in_deleave'
    ),
    path(
        'racklocationdeleave/<int:id>/',
        views.RackLocationDeleave.as_view(),
        name='rack_location_deleave',
    ),
    path(
        'racklocationdeleavemore/',
        views.RackLocationDeleaveMore.as_view(),
        name='rack_location_deleave_all',
    ),
    path('getrackbysn/', views.GetRackBySn.as_view(), name='get_rack_by_sn'),
    path('scacinlist/', views.ScanInList.as_view(), name='scan_in_list'),
]
