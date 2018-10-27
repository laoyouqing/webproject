from django.shortcuts import render
from django.http import JsonResponse
from django.views.generic import View
from django.contrib.auth.decorators import login_required
from redis import StrictRedis
from df_goods.models import *
import json
#封装as_view()的方法mixin
class LoginRequiredMixin(object):
    @classmethod
    def as_view(cls, **initkwargs):
        view = super().as_view(**initkwargs)  #得到要装饰的函数
        return login_required(view)  #手动对函数进行装饰


class CartView(LoginRequiredMixin,View):
    def get(self,request):
        user = request.user
        conn = StrictRedis('192.168.12.186', db=5)
        cart_key = 'cart_%d' % user.id
        cart_dict =conn.hgetall(cart_key)
        skus=[]
        for sku_id,count in cart_dict.items():
           sku=GoodsSKU.objects.get(id=sku_id)
           #给sku动态的添加属性
           sku.count=count
           skus.append(sku)
        context={'page_name':1,'skus':skus}
        return render(request,'df_cart/cart.html',context)


class CartAddView(View):
    '''购物车记录添加'''

    def post(self, request):
        '''购物车记录添加'''
        user = request.user
        if not user.is_authenticated():
            return JsonResponse({'res': 0, 'errmsg': '请先登录'})

        # 接收数据
        sku_id = request.POST.get('sku_id')
        count = request.POST.get('count')


        # 数据验证
        if not all([sku_id, count]):
            return JsonResponse({'res': 1, 'errmsg': '数据不完整'})

        # 验证添加的商品数量
        try:
            count = int(count)
        except Exception as e:
            return JsonResponse({'res': 2, 'errmsg': '商品数目出错'})

        # 验证商品是否存在
        try:
            sku = GoodsSKU.objects.get(id=sku_id)
        except GoodsSKU.DoesNotExist:
            return JsonResponse({'res': 3, 'errmsg': '商品不存在'})

        # 业务处理：添加购物车记录
        conn = StrictRedis('192.168.12.186', db=5)
        cart_key = 'cart_%d' % user.id
        # 先尝试获取sku_id的值 ->  hget cart_key 属性
        # 如果sku_id在hash中不存在，hget返回None
        cart_count = conn.hget(cart_key, sku_id)
        if cart_count:
            # 添加购物车中商品的数目
            count += int(cart_count)

        # 验证库存

        if count > sku.stock:
            return JsonResponse({'res': 4, 'errmsg': '库存不足'})

        # 设置hash中sku_id对应的值
        # hset-> 如果sku_id已经存在，更新数据,如果sku_id不存在,添加数据
        conn.hset(cart_key, sku_id, count)

        # 计算用户购物车商品的数目条
        total_count = get_cart_count(user)


        # 反应应答
        return JsonResponse({'res': 5, 'total_count': total_count, 'message': '添加成功'})


def get_cart_count(user):
    '''获取用户的购物车商品的总数'''

    #保存用户购物车中商品的总数目
    total_count=0

    if user.is_authenticated():
        #连接redis
        conn=StrictRedis('192.168.12.186',db=5)
        #key
        cart_key='cart_%d'%user.id
        #获取 信息
        cart_dict=conn.hgetall(cart_key)
        print('cart_dict',cart_dict)

        #便利获取商品的信息
        for sku_id,count in cart_dict.items():
            total_count+=int(count)

    return total_count

'''删除购物车'''
class DeleteCartView(View):
    def post(self, request):
        # 接收参数：sku_id
        sku_id = request.POST.get('sku_id')
        # 校验参数：not，判断是否为空
        if not sku_id:
            return JsonResponse({'code': 1, 'message': '参数错误'})

        redis_conn= StrictRedis('192.168.12.186',db=5)
        user_id = request.user.id
        redis_conn.hdel('cart_%s' % user_id, sku_id)

        return JsonResponse({'code': 0, 'message': '删除成功'})


def count(request):
    total_count=get_cart_count(request.user)
    return JsonResponse({'total_count':total_count})


class CartUpdateView(View):
    '''购物车记录更新'''
    def post(self,request):

        user = request.user
        if not user.is_authenticated():
            return JsonResponse({'res': 0, 'errmsg': '请先登录'})

        # 接收数据
        sku_id = request.POST.get('sku_id')
        count = request.POST.get('count')


        # 数据验证
        if not all([sku_id, count]):
            return JsonResponse({'res': 1, 'errmsg': '数据不完整'})

        # 验证添加的商品数量
        try:
            count = int(count)
        except Exception as e:
            return JsonResponse({'res': 2, 'errmsg': '商品数目出错'})

        # 验证商品是否存在
        try:
            sku = GoodsSKU.objects.get(id=sku_id)
        except GoodsSKU.DoesNotExist:
            return JsonResponse({'res': 3, 'errmsg': '商品不存在'})

        # 业务处理：添加购物车记录
        conn = StrictRedis('192.168.12.186', db=5)
        cart_key = 'cart_%d' % user.id


        # 验证库存
        if count > sku.stock:
            count = conn.hget(cart_key, sku_id).decode('utf-8')
            return JsonResponse({'res': 4, 'errmsg': '库存不足','count':count})

        # 设置hash中sku_id对应的值
        # hset-> 如果sku_id已经存在，更新数据,如果sku_id不存在,添加数据
        conn.hset(cart_key, sku_id, count)
        count=conn.hget(cart_key,sku_id).decode('utf-8')

        # 反应应答
        return JsonResponse({'res': 5, 'count': count, 'message': '添加成功'})