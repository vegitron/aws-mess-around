# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='BuildData',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('project', models.CharField(max_length=200, db_index=True)),
                ('use', models.CharField(max_length=200, db_index=True)),
                ('role', models.CharField(max_length=200, db_index=True)),
                ('data_field', models.CharField(max_length=200, db_index=True)),
                ('value', models.CharField(max_length=1024)),
            ],
        ),
        migrations.AlterUniqueTogether(
            name='builddata',
            unique_together=set([('project', 'use', 'role', 'data_field')]),
        ),
    ]
