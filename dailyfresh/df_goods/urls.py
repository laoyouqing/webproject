from django.conf.urls import url
from . import views
from .views import IndexView,DetailView

urlpatterns=[
    url(r'^$',IndexView.as_view(),name='index'),
    url(r'^detail/(\d+)$',DetailView.as_view(),name='detail'),
    url(r'^list/(\d+)_(\d+)_(\d+)/$',views.list,name='list'),
    url(r'^comment/(\d+)$',views.comment,name='comment')

]