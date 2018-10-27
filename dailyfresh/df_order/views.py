from django.shortcuts import render,redirect
from django.views.generic import View
from django.http import JsonResponse
from df_user.models import *
from df_goods.models import *
from df_order.models import *
from redis import  StrictRedis
import datetime
from django.db import transaction
from alipay import AliPay
from django.conf import settings
import os
from django.core.urlresolvers import reverse


class OrderView(View):

    def post(self,request):
        '''提交订单页面显示'''
        user=request.user

        #获取参数sku_ids
        sku_ids=request.POST.getlist('sku_ids')
        print((sku_ids))

        if not sku_ids:
            return redirect('/cart/')

        conn=StrictRedis('192.168.12.186',db=5)
        cart_key='cart_%d'%user.id

        skus=[]
        #保存商品的总价格和总件数
        total_count=0
        total_price=0
        #遍历sku_ids获取用户要购买的商品的信息
        for sku_id in sku_ids:
            sku=GoodsSKU.objects.get(id=sku_id)
            print(sku)
            #获取用户要购买的商品的数量
            count=conn.hget(cart_key,sku_id).decode('utf-8')
            print(count)
            #计算商品的小计
            amount=sku.price*int(count)

            #动态的给sku添加属性count
            sku.count=count
            sku.amount=amount

            skus.append(sku)
            print(skus)

            #累计商品的总件数总价格
            total_count+=int(count)
            total_price+=amount

        #运费
        transit_price=10

        #实付款
        total_pay=total_price+transit_price

        sku_ids='.'.join(sku_ids)

        # 用户的所有地址
        address = Address.objects.filter(user=user)

        context={
            'skus':skus,
            'total_count':total_count,
            'total_price':total_price,
            'total_pay':total_pay,
            'transit_price':transit_price,
            'sku_ids':sku_ids,
            'page_name': 1,
            'address': address,
        }

        return render(request,'df_order/place_order.html',context)


class CommitView(View):
    #开启事务


    @transaction.atomic
    def post(self,request):
        user=request.user
        if not user.is_authenticated():
            return JsonResponse({'res': 0, 'errmsg': '请先登录'})

        # 接收数据
        addr_id = request.POST.get('addr_id')
        pay_method = request.POST.get('pay_method')
        sku_ids = request.POST.get('sku_ids')


        # 数据验证
        if not all([addr_id, pay_method,sku_ids]):
            return JsonResponse({'res': 1, 'errmsg': '数据不完整'})

        # # 验证支付方式
        # try:
        #     pay_method = int(pay_method)
        # except Exception as e:
        #     return JsonResponse({'res': 2, 'errmsg': '非法的支付方式1'})

        if pay_method not in OrderInfo.PAY_METHODS.keys():
            return JsonResponse({'res': 2, 'errmsg': '非法的支付方式2'})


        #校验地址
        try:
            addr=Address.objects.get(id=addr_id)
        except Address.DoesNotExist:
            return JsonResponse({'res': 3, 'errmsg': '地址非法'})


        #创建订单核心业务
        #组织参数
        #订单id
        order_id=datetime.datetime.today().strftime('%Y%m%d%H%M%S')+str(user.id)

        #运费
        transit_price=10

        #总数目和总金额
        total_count=0
        total_price=0


        try:
            #设置保存点
            save_point = transaction.savepoint()

            order=OrderInfo.objects.create(
                order_id=order_id,
                user=user,
                addr=addr,
                pay_method=pay_method,
                total_count=total_count,
                total_price=total_price,
                transit_price=transit_price
            )
            #用户订单有几个商品。需要向OrderGoods中插入几条数据
            conn=StrictRedis('192.168.12.186',db=5)
            cart_key = 'cart_%d' % user.id

            sku_ids=sku_ids.split('.')
            for sku_id in sku_ids:
                #获取商品信息
                for i in range(3):
                    try:
                        #悲观锁
                        #sku=GoodsSKU.objects.select_for_update().get(id=sku_id)

                        #使用乐观锁
                        sku=GoodsSKU.objects.get(id=sku_id)
                        origin_stock=sku.stock   #原始库存
                        origin_sales=sku.sales   #原始销量
                    except:
                        #回滚
                        transaction.savepoint_rollback(save_point)
                        return JsonResponse({'res': 4, 'errmsg': '商品不存在'})

                    #获取要购买的商品的数量
                    count=conn.hget(cart_key,sku_id).decode('utf-8')

                    #判断库存
                    if int(count) > sku.stock:
                        transaction.savepoint_rollback(save_point)
                        return JsonResponse({'res': 6, 'errmsg': '库存不足'})


                    print('uid:%s,stock:%s,i=%s'%(user.id,sku.stock,i))
                    # import time
                    # time.sleep(10)

                    # 更新商品的库存和销量
                    stock=origin_stock-int(count)
                    sales=origin_sales+int(count)
                    ret=GoodsSKU.objects.filter(id=sku_id,stock=origin_stock).update(stock=stock,sales=sales)

                    print('uid:%s,stock:%s,num=%s' % (user.id, sku.stock,ret))

                    if ret==0:
                        if i==2:
                            transaction.savepoint_rollback(save_point)
                            return JsonResponse({'res': 8, 'errmsg': 'xxxxxx'})
                        #退出本次循环
                        continue

                    OrderGoods.objects.create(
                        order=order,
                        sku=sku,
                        count=count,
                        price=sku.price
                    )



                    #累计订单的总数量和总价格
                    amount=sku.price*int(count)
                    total_count+=int(count)
                    total_price+=amount

                    #结束循环
                    break

            #更新订单信息表中的总数量和总价格
            order.total_count=total_count
            order.total_price=total_price
            order.save()
            #提交事务
            transaction.savepoint_commit(save_point)
        except Exception as e:
            #回滚
            transaction.savepoint_rollback(save_point)
            return JsonResponse({'res': 7, 'errmsg': '下单失败'})

        #清除用户购物车对应的记录
        conn.hdel(cart_key,*sku_ids)

        return JsonResponse({'res': 5, 'errmsg': '创建成功'})


def buy(request):
    count=request.POST.get('num_show')
    sku_id=request.POST.get('sku_id')
    print(count,sku_id)

    user=request.user

    conn = StrictRedis('192.168.12.186', db=5)
    cart_key = 'cart_%d' % user.id

    cart_count = conn.hget(cart_key, sku_id)
    if cart_count:
        # 添加购物车中商品的数目
        count1=int(count) + int(cart_count)
    else:
        count1=int(count)

    conn.hset(cart_key, sku_id, count1)

    sku = GoodsSKU.objects.get(id=sku_id)

    skus = []
    # 保存商品的总件数
    total_count = count


    # 计算商品的小计
    amount = sku.price * int(count)

    # 动态的给sku添加属性count
    sku.count = count
    sku.amount = amount

    skus.append(sku)
    print(skus)


    # 运费
    transit_price = 10

    # 实付款
    total_pay = amount + transit_price

    sku_ids = '.'.join(sku_id)

    # 用户的所有地址
    address = Address.objects.filter(user=user)

    context = {
        'skus': skus,
        'total_count': total_count,
        'total_price': amount,
        'total_pay': total_pay,
        'transit_price': transit_price,
        'sku_ids': sku_ids,
        'page_name': 1,
        'address': address,
    }

    return render(request, 'df_order/place_order.html', context)


class OrderPayView(View):
    '''订单支付'''

    def post(self, request):
        # 用户是否登录
        user = request.user
        if not user.is_authenticated():
            return JsonResponse({'res': 0, 'errmsg': '请先登录'})
        # 接收参数
        order_id = request.POST.get('order_id')

        # 校验参数
        if not order_id:
            return JsonResponse({'res': 1, 'errmsg': '数据不完整'})
        try:
            order = OrderInfo.objects.get(user=user,
                                          order_id=order_id,
                                          pay_method=3,
                                          order_status=1)
        except Exception as e:
            return JsonResponse({'res': 2, 'errmsg': '订单错误'})

        # 业务初始化
        # 使用Python  sdk 调用支付宝接口
        alipay = AliPay(
            appid="2016092000551361",  # 应用id
            app_notify_url=None,  # 默认回调url
            app_private_key_path=os.path.join(settings.BASE_DIR, 'df_order/app_private_key.pem'),
            alipay_public_key_path=os.path.join(settings.BASE_DIR, 'df_order/alipay_public_key.pem'),
            # 支付宝的公钥，验证支付宝回传消息使用，不是你自己的公钥,
            sign_type="RSA2",  # RSA 或者 RSA2
            debug=True  # 默认False
        )

        # 调用支付接口
        # 电脑网站支付，需要跳转到https://openapi.alipaydev.com/gateway.do? + order_string
        total_pay = order.total_price + order.transit_price  # Decimal
        order_string = alipay.api_alipay_trade_page_pay(
            out_trade_no=order_id,  # 订单id
            total_amount=str(total_pay),  # 支付总金额
            subject='天天生鲜%s' % order_id,
            return_url=None,
            notify_url=None  # 可选, 不填则使用默认notify url
        )

        # 返回应答
        pay_url = 'https://openapi.alipaydev.com/gateway.do?' + order_string
        return JsonResponse({'res': 3, 'pay_url': pay_url})


class CheckPayView(View):
    '''查看订单支付结果'''
    def post(self,request):
        # 用户是否登录
        user = request.user
        if not user.is_authenticated():
            return JsonResponse({'res':0,'errmsg':'请先登录'})

        # 接收参数
        order_id = request.POST.get('order_id')

        #  校验参数
        if not order_id:
            return JsonResponse({'res':1,'errmsg':'无效的订单'})
        try:
            order = OrderInfo.objects.get(order_id=order_id,
                                          user=user,
                                          pay_method=3,
                                          order_status=1)
        except Exception as e:
            return JsonResponse({'res':2,'errmsg':'订单错误'})
        # 业务初始化:使用python sdk调用支付宝的支付接口
        # 初始化
        alipay = AliPay(
            appid="2016092000551361",  # 应用id
            app_notify_url=None,  # 默认回调url
            app_private_key_path=os.path.join(settings.BASE_DIR, 'df_order/app_private_key.pem'),
            alipay_public_key_path=os.path.join(settings.BASE_DIR, 'df_order/alipay_public_key.pem'),
            # 支付宝的公钥，验证支付宝回传消息使用，不是你自己的公钥,
            sign_type="RSA2",  # RSA 或者 RSA2
            debug=True  # 默认False
        )
        # 调用支付宝的交易查询接口
        while True:
            response = alipay.api_alipay_trade_query(order_id)
            code = response.get('code')

            if code == '10000' and response.get('trade_status') == 'TRADE_SUCCESS':
                # 支付成功
                # 获取支付宝交易号
                trade_no = response.get('trade_no')
                # 更新订单状态
                order.trade_no = trade_no
                order.order_status = 4  # 待评价
                order.save()
                # 返回结果
                return JsonResponse({'res': 3, 'message': '支付成功'})
            elif code == '40004' or (code == '10000' and response.get('trade_status') == 'WAIT_BUYER_PAY'):
                # 等待买家付款
                # 业务处理失败，可能一会就会成功
                import time
                time.sleep(5)
                continue
            else:
                # 支付出错
                print(code)
                return JsonResponse({'res': 4, 'errmsg': '支付失败'})



def comment(request,order_id):
    order=OrderInfo.objects.get(order_id=order_id)
    order_goods=OrderGoods.objects.filter(order=order)
    print(order_goods)
    context={
        'title': '天天生鲜订单页面',
        'page_name': 1, 'page': 2,
        'order_goods':order_goods,
        'order':order,
    }
    return render(request,'df_order/comment.html',context)



def comment1(request,sku_id):
    if request.method=='GET':
        sku=GoodsSKU.objects.get(id=sku_id)
        return render(request,'df_order/comment1.html',{'sku':sku,'page': 2,'page_name': 1,})

    if request.method=='POST':
        content=request.POST.get('comment')
        sku = GoodsSKU.objects.get(id=sku_id)
        Comment.objects.create(content=content,sku=sku)
        return redirect(reverse('goods:detail',args=[sku_id]))


