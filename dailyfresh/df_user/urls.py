from django.conf.urls import url
from . import views
from .views import LoginView,ActiveView,ForgetView,ResetView

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
    url(r'^order/$',views.order,name='order'),
    url(r'^site/$',views.site,name='site'),
]