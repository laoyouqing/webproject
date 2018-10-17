# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('df_user', '0003_auto_20181016_1207'),
    ]

    operations = [
        migrations.CreateModel(
            name='Area',
            fields=[
                ('id', models.AutoField(serialize=False, primary_key=True, verbose_name='ID', auto_created=True)),
                ('title', models.CharField(max_length=20)),
                ('parea', models.ForeignKey(blank=True, null=True, to='df_user.Area')),
            ],
            options={
                'db_table': 'df_area',
                'verbose_name_plural': '省市区',
                'verbose_name': '省市区',
            },
        ),
    ]
