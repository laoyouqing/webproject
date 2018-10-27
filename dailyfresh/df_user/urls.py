from django.conf.urls import url
from . import views
from .views import LoginView,ActiveView,ForgetView,ResetView,EditorView,AddView

urlpatterns=[
    url(r'^register/$',views.register,name='register'),
    url(r'^register_exist/$',views.register_exist,name='register_exist'),

    url(r'^login/$',LoginView.as_view(),name='login'),
    url(r'^forget/$',ForgetView.as_view(),name='forget'),
    url(r'^reset/(.*)$',ResetView.as_view(),name='reset'),

    url(r'^logout_view/$',views.logout_view,name='logout_view'),

    url(r'^active/(?P<token>.*)$',ActiveView.as_view(),name='active'), #用户激活

    url(r'^veridate_code/$',views.veridate_code,name='veridate_code'),
    url(r'^verity/$',views.verity,name='verity'),

    url(r'^info/$',views.info,name='info'),
    url(r'^order/(\d+)/$',views.order,name='order'),
    url(r'^site/$',views.site,name='site'),

    url(r'^address_handler/$',views.address_handler,name='address_handler'),

    url(r'^editor/(\d+)/$',EditorView.as_view(),name='editor'),
    url(r'^delete/(\d+)/$',views.delete,name='delete'),
    url(r'^add/$',AddView.as_view(),name='add'),

    url(r'^area$',views.area,name='area'),
    url(r'^pro/$',views.pro,name='pro'),
    url(r'^city/(\d+)/$',views.city,name='city'),
]