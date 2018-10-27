# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('df_goods', '0002_auto_20181018_2052'),
    ]

    operations = [
        migrations.CreateModel(
            name='Comment',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('create_time', models.DateTimeField(auto_now_add=True, verbose_name='创建时间')),
                ('update_time', models.DateTimeField(auto_now=True, verbose_name='更新时间')),
                ('is_delete', models.BooleanField(verbose_name='删除标记', default=False)),
                ('content', models.CharField(max_length=255, verbose_name='评论内容')),
                ('reply', models.ForeignKey(null=True, to='df_goods.Comment', verbose_name='回复评论')),
                ('sku', models.ForeignKey(to='df_goods.GoodsSKU', verbose_name='商品sku')),
            ],
            options={
                'abstract': False,
            },
        ),
    ]
