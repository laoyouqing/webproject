from django.conf.urls import url
from . import views
from .views import OrderView,CommitView,OrderPayView,CheckPayView
from django.contrib.auth.decorators import login_required

urlpatterns=[
    url(r'^$',login_required(OrderView.as_view()),name='order'),
    url(r'^commit/$',login_required(CommitView.as_view()),name='commit'),
    url(r'^buy/$',views.buy,name='buy'),
    url(r'^pay/$',OrderPayView.as_view(),name='pay'),
    url(r'^check/$',CheckPayView.as_view(),name='check'),
    url(r'^comment/(\d+)$',views.comment,name='comment'),
    url(r'^comment1/(\d+)$',views.comment1,name='comment1'),

]