from django.conf.urls import url
from . import views
from .views import OrderView
from django.contrib.auth.decorators import login_required

urlpatterns=[
    url(r'^$',login_required(OrderView.as_view()),name='order')
]