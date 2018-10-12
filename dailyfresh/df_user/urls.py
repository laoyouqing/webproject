from django.conf.urls import url
from . import views
from .views import LoginView

urlpatterns=[
    url(r'^register/$',views.register,name='register'),
    url(r'^register_exist/$',views.register_exist,name='register_exist'),

    url(r'^login/$',LoginView.as_view(),name='login'),

    url(r'^veridate_code/$',views.veridate_code,name='veridate_code'),
    url(r'^verity/$',views.verity,name='verity'),

    url(r'^info/$',views.info,name='info'),
    url(r'^order/$',views.order,name='order'),
    url(r'^site/$',views.site,name='site'),
]