from django.shortcuts import render
from df_user.models import User
from django.contrib.auth.decorators import login_required

def index(request):
    context = {'title': '天天生鲜-首页', 'guest_cart': 1}
    return render(request,'df_goods/index.html',context)

@login_required
def detail(request):
    context = {'title': '天天生鲜-详情页面', 'guest_cart': 1}
    return render(request,'df_goods/detail.html',context)
@login_required
def list(request):
    context = {'title': '天天生鲜-列表页面', 'guest_cart': 1}
    return render(request,'df_goods/list.html',context)