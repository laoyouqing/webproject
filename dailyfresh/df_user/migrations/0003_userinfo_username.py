# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('df_user', '0002_userinfo'),
    ]

    operations = [
        migrations.AddField(
            model_name='userinfo',
            name='username',
            field=models.CharField(max_length=30, default=1),
            preserve_default=False,
        ),
    ]
