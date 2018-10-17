from django.conf.urls import url
from . import views
from .views import IndexView

urlpatterns=[
    url(r'^$',views.index,name='index'),
    url(r'^detail/$',views.detail,name='detail'),
    url(r'^list/$',views.list,name='list'),

    url(r'^indextest/$',IndexView.as_view())
]