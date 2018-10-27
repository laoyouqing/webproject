from django.conf.urls import url
from . import views
from .views import CartView,CartAddView,CartUpdateView,DeleteCartView


urlpatterns=[
    url(r'^$',CartView.as_view(),name='cart'),
    url(r'^add/$',CartAddView.as_view(),name='add'),  #购物车记录添加
    url(r'^delete/$',DeleteCartView.as_view(),name='delete'),
    url(r'^update/$',CartUpdateView.as_view(),name='update'),
    url(r'^count/$',views.count,name='count'),
]