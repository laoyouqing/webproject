from django.shortcuts import render
from django.views.generic import View
from django.contrib.auth.decorators import login_required

#封装as_view()的方法mixin
class LoginRequiredMixin(object):
    @classmethod
    def as_view(cls, **initkwargs):
        view = super().as_view(**initkwargs)  #得到要装饰的函数
        return login_required(view)  #手动对函数进行装饰


class CartView(LoginRequiredMixin,View):
    def get(self,request):
        context={'page_name':1}
        return render(request,'df_cart/cart.html',context)
