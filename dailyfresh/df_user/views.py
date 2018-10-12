from django.shortcuts import render,redirect
from django.core.urlresolvers import reverse
from django.http import JsonResponse,HttpResponse
import hashlib
from .models import *
import random
from  PIL import Image,ImageFont,ImageDraw
from io import BytesIO
from django.views.generic import View
from django.contrib.auth import authenticate

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

        return redirect(reverse('user:login'))

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
                resp = redirect('/user/info')

                # 记住用户名
                if remember == '1':

                    resp.set_cookie('uname', uname)
                else:
                    resp.set_cookie('uname', '', 0)
                request.session['user_id'] = user[0].id
                request.session['user_name'] = uname
                return resp
            else:
                context = {'title': '用户登录', 'error_name': 0, 'error_pwd': 1, 'uname': uname, 'upwd': upwd}
                return render(request, 'df_user/login.html', context)
        else:
            context = {'title': '用户登录', 'error_name': 1, 'error_pwd': 0, 'uname': uname, 'upwd': upwd}
            return render(request, 'df_user/login.html', context)


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
    #设置session
    request.session['veridate_code']=rand_str

    buf=BytesIO()
    im.save(buf,'png')
    return HttpResponse(buf.getvalue(), 'image/png')


def info(request):
    context = {'title': '天天生鲜订单页面', 'page_name': 1}
    return render(request,'df_user/user_center_info.html',context)

def order(request):
    context={'title':'天天生鲜订单页面','page_name':1}
    return render(request,'df_user/user_center_order.html',context)

def site(request):
    context = {'title': '天天生鲜订单页面', 'page_name': 1}
    return render(request,'df_user/user_center_site.html',context)