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
        url='http://192.168.12.186:8887/user/active/%s'%token

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
                url = 'http://192.168.12.186:8887/user/reset/%s' % token


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
    user_id = request.session.get('_auth_user_id')
    # user_id=request.user.id
    user = User.objects.get(id=user_id)
    userinfo=user.userinfo_set.all()
    if userinfo:
        userinfo = userinfo[0]
    context = {'title': '天天生鲜订单页面', 'page_name': 1,'userinfo':userinfo,'page':1}
    return render(request,'df_user/user_center_info.html',context)

@login_required
def order(request):
    context={'title':'天天生鲜订单页面','page_name':1,'page':2}
    return render(request,'df_user/user_center_order.html',context)

@login_required
def site(request):
    user_id = request.session.get('_auth_user_id')
    # user_id=request.user.id

    if request.method=='GET':
        user=User.objects.get(id=user_id)
        userinfo=user.userinfo_set.all()
        if userinfo:
            userinfo=userinfo[0]

    if request.method=='POST':
        id= request.POST.get('id')
        username = request.POST.get('username')
        address = request.POST.get('address')
        postcode = request.POST.get('postcode')
        phone = request.POST.get('phone')
        #无用户信息
        if id!='':
            # 得到用户信息，更改
            userinfo = UserInfo.objects.get(id=id)
            if len(phone) > 11 or len(postcode) > 6 or len(username) > 30 or len(address) > 100:
                context = {'title': '天天生鲜用户中心', 'page_name': 1, 'userinfo': userinfo, 'page': 3, 'info': '信息有误,请重新输入'}
                return render(request, 'df_user/user_center_site.html', context)
            try:
                userinfo.user_id=user_id
                userinfo.username=username
                userinfo.address=address
                userinfo.postcode=postcode
                userinfo.phone=phone
                userinfo.save()
            except:
                pass

        else:
           userinfo=UserInfo.objects.create(username=username,address=address,postcode=postcode,phone=phone,user_id=user_id)

    context = {'title': '天天生鲜用户中心', 'page_name': 1,'userinfo':userinfo,'page':3,'info':info}
    return render(request,'df_user/user_center_site.html',context)

