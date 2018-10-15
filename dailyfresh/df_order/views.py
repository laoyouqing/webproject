from django.shortcuts import render
from django.views.generic import View

class OrderView(View):
    def get(self,request):
        context={'page_name':1}
        return render(request,'df_order/place_order.html',context)
