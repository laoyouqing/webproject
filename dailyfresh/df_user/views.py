from django.shortcuts import render,redirect
from django.core.urlresolvers import reverse
from django.http import JsonResponse,HttpResponse
import hashlib
from .models import *
import random
from  PIL import Image,ImageFont,ImageDraw
from io import BytesIO
from django.views.generic import View
from django.contrib.auth import authenticate,login,logout
from itsdangerous import TimedJSONWebSignatureSerializer as TJSS ,BadSignature,SignatureExpired
from django.core.mail import send_mail
from dailyfresh  import settings
from django.contrib.auth.hashers import make_password
from celery_task.tasks import send_email_task
from django.contrib.auth.decorators import login_required
import re
from redis import StrictRedis
from df_goods.models import *
from df_order.models import *
from django.core.paginator import Paginator



def my_md5(value):
    m=hashlib.md5()
    m.update(value.encode('utf-8'))
    return m.hexdigest()


def register(request):
    if request.method=='GET':
        #注册页面
        return render(request,'df_user/register.html')
    elif request.method=='POST':
        #注册处理
        username = request.POST.get('user_name')
        password = request.POST.get('pwd')
        cpwd = request.POST.get('cpwd')
        email = request.POST.get('email')
        veridate_code = request.POST.get('veridate_code')

        if veridate_code.lower() != request.session.get('veridate_code').lower():
            return redirect(reverse('user:register'))

        # 判断两次密码
        if password != cpwd:
            return redirect(reverse('user:register'))

        # 密码加密
        upwd = my_md5(password)

        # 创建用户
        user=User.objects.create_user(username=username,password=password,email=email)

        #更新
        user.is_active=0
        user.save()

        #加密用户的身份信息，生成激活码
        s=TJSS(settings.SECRET_KEY,3600)
        info={'confirm':user.id}
        token=s.dumps(info).decode()
        url='http://192.168.12.186:8888/user/active/%s'%token

        #发邮件
        subject='天天生鲜欢迎信息'
        message=''  #文本内容
        sender=settings.EMAIL_FROM
        receiver=[email] #收件人
        html_message='<h1>%s,欢迎成为天天生鲜注册会员</h1>请点击下面链接激活你的账户<br/><a href="%s">%s</a>'%(username,url,url)

        send_email_task.delay(subject, message, sender, receiver, html_message)  #发布异步任务

        return render(request,'df_user/active.html')


class ActiveView(View):
    '''用户激活'''
    def get(self,request,token):
        '''进行用户激活'''
        #进行解密，获取要激活的用户的信息
        s=TJSS(settings.SECRET_KEY,3600)
        try:
            info=s.loads(token)
            #获取用户的id
            user_id=info['confirm']

            #根据id获取用户
            user=User.objects.get(id=user_id)
            #更新激活用户
            user.is_active=1
            user.save()
            return redirect('/user/login')
        except SignatureExpired as e:
            #激活链接已过期
            return HttpResponse('激活链接已过期')
        except BadSignature as e:
            return HttpResponse('激活链接非法')

#验证验证码
def verity(request):
    veridate_code=request.GET.get('veridate_code','').lower()
    if veridate_code!=request.session.get('veridate_code').lower( ):
        return JsonResponse({'errmsg':1})
    else:
        return JsonResponse({'errmsg':0})

#判断用户名是否存在
def register_exist(request):
    uname=request.GET.get('uname')
    count=User.objects.filter(username=uname).count()
    return JsonResponse({'count':count})



#类视图
class LoginView(View):
    def get(self,request):
        uname = request.COOKIES.get('uname', '')
        context = {'title': '用户登录', 'error_name': 0, 'error_pwd': 0, 'uname': uname}
        return render(request, 'df_user/login.html', context)

    def post(self,request):
        uname = request.POST.get('username')
        upwd = request.POST.get('pwd')
        remember = request.POST.get('remember')

        user = User.objects.filter(username=uname)

        # 判断用户是否存在
        if user:
            #验证用户
            user1=authenticate(username=uname,password=upwd)
            if user1 is not None:
                if user1.is_active:
                    resp = redirect('/user/info')
                    url = request.GET.get('next')
                    if url:
                        resp = redirect(url)
                    else:
                        resp = redirect('/goods/')

                    # 记住用户名
                    if remember == '1':
                        resp.set_cookie('uname', uname)
                    else:
                        resp.set_cookie('uname', '', 0)
                    #登录成功设置session
                    # request.session['id'] = user[0].id
                    login(request,user1)   #将用户id(_auth_user_id)保存在会话中
                    return resp
                else:
                    return render(request,'df_user/active.html',{'info':'还未激活，无法登录'})
            else:
                context = {'title': '用户登录', 'error_name': 0, 'error_pwd': 1, 'uname': uname, 'upwd': upwd}
                return render(request, 'df_user/login.html', context)
        else:
            context = {'title': '用户登录', 'error_name': 1, 'error_pwd': 0, 'uname': uname, 'upwd': upwd}
            return render(request, 'df_user/login.html', context)


def logout_view(request):
    #删除session
    logout(request)
    return redirect('/user/login/')


class ForgetView(View):
    def get(self,request):
        return render(request,'df_user/forget.html',{'name_err':0,'email_err':0})

    def post(self,request):
        username=request.POST.get('username','')
        email=request.POST.get('email','')
        #获取用户
        user=User.objects.filter(username=username)
        #判断用户是否存在
        if user:
            if user[0].email==email:
                # 加密用户的身份信息，生成激活码
                s = TJSS(settings.SECRET_KEY, 3600)
                info = {'confirm': user[0].id}
                token = s.dumps(info).decode()
                url = 'http://192.168.12.186:8888/user/reset/%s' % token


                subject = '天天生鲜欢迎信息'
                message = ''  # 文本内容
                sender = settings.EMAIL_FROM
                receiver = [email]  # 收件人
                html_message = '<h1>%s</h1>请点击下面链接修改密码<br/><a href="%s">%s</a>' % (username, url, url)
                #发送邮件
                send_email_task.delay(subject, message, sender, receiver, html_message)
                return render(request,'df_user/success.html')
            else:
                return render(request,'df_user/forget.html',{'username':username,'email':email,'name_err':0,'email_err':1})
        else:
            return render(request,'df_user/forget.html',{'username':username,'email':email,'name_err':1,'email_err':0})

class ResetView(View):
    '''重置密码'''
    def get(self, request, token):
        # 进行解密，获取要激活的用户的信息
        s = TJSS(settings.SECRET_KEY, 3600)
        try:
            info = s.loads(token)
            # 获取用户的id
            user_id = info['confirm']
            # 根据id获取用户
            user = User.objects.get(id=user_id)
            return render(request,'df_user/reset.html',{'user':user,'username':user.username})
        except SignatureExpired as e:
            # 激活链接已过期
            return HttpResponse('激活链接已过期')
        except BadSignature as e:
            return HttpResponse('激活链接非法')

    def post(self,request,token):
        username=request.POST.get('username')
        newpwd1=request.POST.get('newpwd1')
        newpwd2=request.POST.get('newpwd2')
        if newpwd1!=newpwd2:
            return render(request,'df_user/reset.html',{'msg':'密码不一致','username':username})
        else:
            #根据id获取用户，重置密码
            user=User.objects.get(id=token)
            user.set_password(newpwd1)
            # user.password=make_password(newpwd1)
            user.save()
            return redirect('/user/login/')

#生成验证码
def veridate_code(request):
    # 定义变量，用于画面的背景色、宽、高
    bgcolor = (random.randrange(20, 100), random.randrange(
        20, 100), 255)
    width = 100
    height = 25
    # 创建画面对象
    im = Image.new('RGB', (width, height), bgcolor)
    # 创建画笔对象
    draw = ImageDraw.Draw(im)
    # 调用画笔的point()函数绘制噪点
    for i in range(0, 100):
        xy = (random.randrange(0, width), random.randrange(0, height))
        fill = (random.randrange(0, 255), 255, random.randrange(0, 255))
        draw.point(xy, fill=fill)
    # 定义验证码的备选值
    str1 = 'ABCD123EFGHIJK456LMNOPQRS789TUVWXYZ0'
    # 随机选取4个值作为验证码
    rand_str = ''
    for i in range(0, 4):
        rand_str += str1[random.randrange(0, len(str1))]
    # 构造字体对象
    font = ImageFont.truetype('FreeMono.ttf', 23)
    # 构造字体颜色
    fontcolor = (255, random.randrange(0, 255), random.randrange(0, 255))
    # 绘制4个字
    draw.text((5, 2), rand_str[0], font=font, fill=fontcolor)
    draw.text((25, 2), rand_str[1], font=font, fill=fontcolor)
    draw.text((50, 2), rand_str[2], font=font, fill=fontcolor)
    draw.text((75, 2), rand_str[3], font=font, fill=fontcolor)
    # 释放画笔
    del draw
    #设置session  存在redis中redis服务器必须启动
    request.session['veridate_code']=rand_str

    buf=BytesIO()
    im.save(buf,'png')
    return HttpResponse(buf.getvalue(), 'image/png')

@login_required
def info(request):
    skus = []
    user = request.user
    redis_conn=StrictRedis(host='192.168.12.186',port=6379)
    #判断键是否存在
    if redis_conn.exists('history_%s'%user.id):
        #判断键是否大于4
        if redis_conn.llen('history_%s'%user.id)>=4:
            history=redis_conn.lrange('history_%s'%user.id,0,4)
        else:
            history = redis_conn.lrange('history_%s' % user.id, 0, -1)
        #获取最近浏览的四个商品
        for sku_id in history:
            sku=GoodsSKU.objects.get(id=sku_id)
            skus.append(sku)

    if request.method == 'GET':
        try:
            address = Address.objects.get(user=user, is_default=True)
        except:
            address = None

    context = {'title': '天天生鲜订单页面', 'page_name': 1,'address':address,'page':1,'skus':skus}
    return render(request,'df_user/user_center_info.html',context)

@login_required
def order(request,page):
    #获取用户的订单信息
    user=request.user
    orders=OrderInfo.objects.filter(user=user).order_by('-create_time')

    #遍历获取订单的信息
    for order in orders:
        order_skus=OrderGoods.objects.filter(order_id=order.order_id)

        #遍历获取skus的小计
        for order_sku in order_skus:
            amount=order_sku.price*order_sku.count
            #动态添加amount
            order_sku.amount=amount

        #动态的给订单添加属性，保存订单商品的信息
        order.order_skus=order_skus
        # print(order.order_skus)


    #分页
    paginator = Paginator(orders, 1)

    try:
        page=int(page)
    except Exception as e:
        page=1

    if page>paginator.num_pages:
        page=1

    my_page = paginator.page(page)

    now_page = int(page)
    # 获取总页数
    num_pages = paginator.num_pages

    # 分页页数显示计算
    # 是否是前三后三页
    if num_pages <= 5:
        page_list = paginator.page_range
    elif now_page <= 3:
        page_list = range(1, 6)
    elif now_page >= num_pages - 2:
        page_list = range(num_pages - 4, num_pages + 1)
    else:
        page_list = range(now_page - 2, now_page + 3)


    context={'title':'天天生鲜订单页面',
             'page_name':1,'page':2,
             'page_list':page_list,
             'my_page':my_page
             }

    return render(request,'df_user/user_center_order.html',context)

@login_required
def site(request):
    user = request.user
    if request.method=='GET':
        address1 = Address.objects.filter(user=user)
        try:
            address=Address.objects.get(user=user,is_default=True)
        except:
            address=None
        context = {'title': '天天生鲜用户中心', 'page_name': 1, 'address': address, 'page': 3, 'info': info,'address1':address1}
        return render(request, 'df_user/user_center_site.html', context)


def address_handler(request):
    id=request.GET.get('id')
    try:
        user=request.user
        address = Address.objects.get(user=user, is_default=True)
        address.is_default = False
        address.save()
    except:
        pass
    address1=Address.objects.get(id=id)
    address1.is_default=True
    address1.save()
    return redirect('/user/site/')

class EditorView(View):
    def get(self,request,id):
        address=Address.objects.get(id=id)
        addr=address.addr
        #对地址进行分割
        addrlist=addr.split('-')

        #通过区名字拿到对象
        addr=Area.objects.get(title=addrlist[2])
        #获取省市区的id
        did=addr.id
        cid=addr.parea_id
        pid=addr.parea.parea_id

        context = {'title': '编辑地址页面', 'page_name': 1, 'address':address,'addrlist': addrlist, 'page': 3,'pid':pid,'cid':cid,'did':did}
        return render(request,'df_user/editor.html',context)

    def post(self,request,id):
        # 获取省市区的id
        pro_id = request.POST.get('pro_id')
        city_id = request.POST.get('city_id')
        dis_id = request.POST.get('dis_id')
        addr = request.POST.get('address')

        # 根据区的id查询对象
        dis = Area.objects.get(id=dis_id)

        # 获取省市县名
        dtitle = dis.title
        ctitle = dis.parea.title
        ptitle = dis.parea.parea.title


        addr = ('-').join([ptitle, ctitle, dtitle, addr])

        address=Address.objects.get(id=id)
        address.username=request.POST.get('username')
        address.postcode=request.POST.get('postcode')
        address.phone=request.POST.get('phone')
        address.addr=addr
        address.save()
        return redirect('/user/site/')


class AddView(View):
    def get(self,request):
        context = {'title': '天天生鲜用户中心', 'page_name': 1, 'page': 3}
        return render(request,'df_user/add.html',context)
    def post(self,request):
        '''地址的添加'''
        username = request.POST.get('username')
        addr = request.POST.get('address')
        postcode = request.POST.get('postcode')
        phone = request.POST.get('phone')

        #获取省市区的id
        pro_id = request.POST.get('pro_id')
        city_id = request.POST.get('city_id')
        dis_id = request.POST.get('dis_id')

        #根据区的id查询对象
        dis=Area.objects.get(id=dis_id)

        #获取省市县
        dtitle=dis.title
        ctitle=dis.parea.title
        ptitle=dis.parea.parea.title

        addr=('-').join([ptitle,ctitle,dtitle,addr])

        user = request.user
        address1 = Address.objects.filter(user=user)
        try:
            address = Address.objects.get(user=user, is_default=True)
        except:
            address = None

        if len(phone) > 11 or len(postcode) > 6 or len(username) > 30 or len(addr) > 100:
            context = {'title': '天天生鲜用户中心', 'page_name': 1, 'page': 3, 'info': '信息有误,请重新输入', 'address': address,
                       'address1': address1}
            return render(request, 'df_user/user_center_site.html', context)

        if not all([username, addr, postcode, phone,pro_id,city_id,dis_id]):
            context = {'title': '天天生鲜用户中心', 'page_name': 1, 'page': 3, 'info': '数据不完整', 'address': address,
                       'address1': address1}
            return render(request, 'df_user/user_center_site.html', context)

        if not re.match(r'^1[3|4|5|7|8][0-9]{9}$', phone):
            context = {'title': '天天生鲜用户中心', 'page_name': 1, 'page': 3, 'info': '手机格式不正确', 'address': address,
                       'address1': address1}
            return render(request, 'df_user/user_center_site.html', context)

        # 业务逻辑：地址添加
        # 用户新新添加的地址作为默认地址，如果原来有默认地址要取消
        # 获取用户的默认地址
        try:
            address = Address.objects.get(user=user, is_default=True)
            address.is_default = False
            address.save()
        except:
            pass

        address = Address.objects.create(username=username, addr=addr, postcode=postcode, phone=phone,
                                         is_default=True,
                                         user=user)

        return redirect('/user/site/')


def delete(request,id):
    address=Address.objects.get(id=id)
    address.delete()
    return redirect('/user/site')


#省市区选择
def area(request):
    return render(request,'booktest/area.html')


def pro(request):
    prolist=Area.objects.filter(parea__isnull=True)
    list=[]
    for item in prolist:
        list.append([item.id,item.title])
    return JsonResponse({'data':list})

def city(request,id):
    citylist=Area.objects.filter(parea_id=id)
    list=[]
    for item in citylist:
        list.append({'id':item.id,'title':item.title})
    return JsonResponse({'data':list})



