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


class UserInfo(models.Model):
    username=models.CharField(max_length=30)
    address=models.CharField(max_length=100)
    postcode=models.CharField(max_length=6)
    phone=models.CharField(max_length=11)
    user=models.ForeignKey(User)