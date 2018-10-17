from django.db import models

from django.contrib.auth.models import AbstractUser
from db.base_model import BaseModel

'''
继承AbstractUser:用它的属性
继承BaseModel：共有的属性
'''

class User(AbstractUser,BaseModel):
    '''
    用户模型类
    '''
    class Meta:
        db_table='df_user'
        verbose_name='用户'
        verbose_name_plural=verbose_name


class Address(BaseModel):
    '''地址模型类'''
    username=models.CharField(max_length=30)
    addr=models.CharField(max_length=100)
    postcode=models.CharField(max_length=6)
    phone=models.CharField(max_length=11)
    is_default=models.BooleanField(default=False)
    user=models.ForeignKey(User)

    class Meta:
        db_table='df_address'
        verbose_name='地址'
        verbose_name_plural=verbose_name


class Area(models.Model):
    title=models.CharField(max_length=20)
    parea=models.ForeignKey("self",null=True,blank=True)

    class Meta:
        db_table='df_area'
        verbose_name='省市区'
        verbose_name_plural=verbose_name
