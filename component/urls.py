from django.urls import path

from component import views

from public import email,sfcs

urlpatterns = [
    path('scheduler/',email.email_data,name='email_data'),
    path('test/',sfcs.test_webservice,name='test'),
    path('componentlist/',views.ComponentList.as_view(),name='component_list'),
    path('componentdetail/<int:id>/',views.ComponentDetail.as_view(),name='component_detail'),
    path('componentnodedetail/<int:id>/',views.ComponentNodeDetail.as_view(),name='component_node_detail'),
    path('snlist/<int:component_id>/',views.SnList.as_view(),name='sn_list'),
    path('sndetail/<int:id>/',views.Sndetail.as_view(),name='sn_detail'),
    path('pnlist/<int:component_id>/',views.PnList.as_view(),name='pn_list'),
    path('pndetail/<int:id>/',views.Pndetail.as_view(),name='pn_detail'),
    path('molist/<int:component_id>/',views.MoList.as_view(),name='mo_list'),
    path('modetail/<int:id>/',views.Modetail.as_view(),name='mo_detail'),
    # path('modelnamelist/<int:component_id>/',views.ModelNameList.as_view(),name='model_name_list'),
    # path('modelnamedetail/<int:id>/',views.ModelNamedetail.as_view(),name='model_name_detail'),
    path('getcomponentbysn/',views.GetComponentBySn.as_view(),name='get_component_by_sn'),
    # path('getcomponentbypn/',views.GetComponentByPn.as_view(),name='get_component_by_pn'),
    # path('getcomponentbymo/',views.GetComponentByMo.as_view(),name='get_component_by_mo'),
]