from django.shortcuts import render,redirect
from django.http import JsonResponse
from df_user.models import User
from .models import *
from django.views.generic import View
from django.core.paginator import Paginator
from redis import StrictRedis
from django.core.cache import cache
from django.core.urlresolvers import reverse
from df_cart.views import get_cart_count
from redis import StrictRedis

class IndexView(View):
    def get(self, request):
        # 查询全部商品分类
        context=cache.get('cache_index')
        # 初始化购物车数量



        if context==None:
            print('设置缓存')
            types = GoodsType.objects.all()
            goods_banners = IndexGoodsBanner.objects.all().order_by('index')  # 获得轮播图片
            promotion_banners = IndexPromotionBanner.objects.all().order_by('index')  # 获取活动图片
            for type in types:
                # 获取type种类首页分类商品的图片展示信息
                image_banners = IndexTypeGoodsBanner.objects.filter(type=type, display_type=1, ).order_by('index')
                title_banners = IndexTypeGoodsBanner.objects.filter(type=type, display_type=0, ).order_by('index')
                # 动态给type增加属性，分别保存首页分类商品的图片展示信息和文字展示信息
                type.image_banners = image_banners
                type.title_banners = title_banners

            context = {'types': types,
                       'goods_banners': goods_banners,
                       'promotion_banners': promotion_banners,
                       'title': '天天生鲜-首页', 'guest_cart': 1,
                       'total_count':0
                    }
            #设置缓存
            cache.set('cache_index',context,3600)

        user = request.user

        total_count = get_cart_count(user)
        context.update(total_count=total_count)

        return render(request, 'df_goods/index.html', context)



class DetailView(View):
    def get(self,request,id):
        user=request.user
        if user.is_authenticated():
            redis_conn=StrictRedis(host='192.168.12.186',port=6379)
            #删除列表中的id
            redis_conn.lrem('history_%s'%user.id,0,id)
            #把id插入到列表左侧
            redis_conn.lpush('history_%s'%user.id,id)

        #sku下的所有评论
        comments=Comment.objects.filter(sku_id=id,reply_id=None)


        sku=GoodsSKU.objects.get(id=id)
        #sku下的所有图片
        goodimage=GoodImage.objects.filter(sku_id=id)
        #新品
        news=sku.type.goodssku_set.order_by('-id')[0:2]

        #同一个SPU下的所有sku
        skus=GoodsSKU.objects.filter(goods=sku.goods)


        user = request.user

        total_count = get_cart_count(user)




        context = {'title': '天天生鲜-详情页面', 'guest_cart': 1,
                   'sku':sku,'news':news,
                   'goodimage':goodimage,
                   'skus':skus,'comments':comments,
                   'total_count': total_count
                   }
        return render(request,'df_goods/detail.html',context)

    def post(self,request,id):
        comment=request.POST.get('comment')
        reply_comment = request.POST.get('reply_comment')
        reply_id=request.POST.get('reply_id')
        print(reply_id,reply_comment)
        if reply_id:
            Comment.objects.create(content=reply_comment, sku_id=id,reply_id=reply_id)
        if comment!='':
            Comment.objects.create(content=comment,sku_id=id)

        return redirect(reverse('goods:detail',args=[id]))


def list(request,id,pn,sort):
    goodstype=GoodsType.objects.get(id=id)
    news=goodstype.goodssku_set.order_by('-id')[0:2]
    if sort=='1':
        skus=goodstype.goodssku_set.order_by('-id').all()
    elif sort=='2':
        skus = goodstype.goodssku_set.order_by('price').all()
    elif sort=='3':
        skus = goodstype.goodssku_set.order_by('sales').all()

    paginator=Paginator(skus,2)

    my_page=paginator.page(pn)

    now_page = int(pn)
    #获取总页数
    num_pages=paginator.num_pages

    #分页页数显示计算
    #是否是前三后三页
    if num_pages<=5:
        page_list=paginator.page_range
    elif now_page<=3:
        page_list=range(1,6)
    elif now_page>=num_pages-2:
        page_list=range(num_pages-4,num_pages+1)
    else:
        page_list=range(now_page-2,now_page+3)

    user = request.user
    total_count = get_cart_count(user)


    context = {'title': '天天生鲜-列表页面', 'guest_cart': 1,
               'news':news,'sort':sort,
               'goodstype': goodstype,
               'skus':skus,
               'page_list':page_list,
               'my_page':my_page,
               'total_count':total_count
               }
    return render(request,'df_goods/list.html',context)




def comment(request,id):
    comment_id=request.GET.get('comment_id')
    print(comment_id)
    rcomments=Comment.objects.filter(reply_id=comment_id)
    print(rcomments)
    data=[]
    for comment in rcomments:
        data.append({'content':comment.content,'id':comment.id})

    return JsonResponse({'data':data})








