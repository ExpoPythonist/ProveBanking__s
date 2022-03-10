# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import re
import users.models
import django_extensions.db.fields
import med_social.constants
import djorm_pgarray.fields
import vlkjsonfield.fields
import django.utils.timezone
from django.conf import settings
import django.core.validators


class Migration(migrations.Migration):

    dependencies = [
        ('roles', '0001_initial'),
        ('locations', '0001_initial'),
        ('auth', '0001_initial'),
        ('vendors', '0001_initial'),
        ('categories', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='User',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('password', models.CharField(max_length=128, verbose_name='password')),
                ('last_login', models.DateTimeField(default=django.utils.timezone.now, verbose_name='last login')),
                ('is_staff', models.BooleanField(default=False, help_text='Designates whether the user can log into this admin site.', verbose_name='staff status')),
                ('is_active', models.BooleanField(default=True, help_text='Designates whether this user should be treated as active. Unselect this instead of deleting accounts.', verbose_name='active')),
                ('is_superuser', models.BooleanField(default=False, help_text='Designates that this user has all permissions without explicitly assigning them.', verbose_name='superuser status')),
                ('date_joined', models.DateTimeField(default=django.utils.timezone.now, verbose_name='date joined')),
                ('username', models.CharField(default=None, max_length=30, validators=[django.core.validators.RegexValidator(re.compile(b'^^\\w+[\\w+.-]*$'), 'Enter a valid username.', b'invalid')], help_text='30 characters or fewer. Letters, numbers, _ and . (dot) characters', unique=True, verbose_name='username')),
                ('email', models.EmailField(unique=True, max_length=254, verbose_name='email address')),
                ('bio', models.TextField(default=b'', max_length=140)),
                ('meta', vlkjsonfield.fields.VLKJSONField(default=users.models._default_user_meta)),
                ('is_deleted', models.BooleanField(default=False, verbose_name='delete')),
                ('kind', models.PositiveSmallIntegerField(default=2, choices=[(1, b'Client'), (2, b'Vendor')])),
                ('pending_setup_steps', djorm_pgarray.fields.ArrayField(default=[1,3], verbose_name='Pending steps')),
                ('first_login', models.DateTimeField(null=True, blank=True)),
                ('first_name', models.CharField(max_length=30, verbose_name='first name', blank=True)),
                ('last_name', models.CharField(max_length=30, verbose_name='last name', blank=True)),
                ('headline', models.TextField(default=b'', max_length=140, verbose_name='headline', blank=True)),
                ('summary', models.TextField(default=b'', max_length=1023, verbose_name='summary', blank=True)),
                ('resume', models.FileField(null=True, upload_to=users.models._get_resume_upload_path)),
                ('linkedin_profile_url', models.URLField(null=True)),
                ('avg_score', models.DecimalField(null=True, max_digits=2, decimal_places=1, blank=True)),
                ('reviews_count', models.IntegerField(default=0, editable=False)),
                ('categories', models.ManyToManyField(related_name=b'users', to='categories.Category')),
                ('groups', models.ManyToManyField(help_text='The groups this user belongs to. A user will get all permissions granted to each of his/her group.', to='auth.Group', verbose_name='groups', blank=True)),
            ],
            options={
                'abstract': False,
                'verbose_name': 'user',
                'verbose_name_plural': 'users',
            },
            bases=(models.Model, med_social.constants.OnboardingConstantsMixin, med_social.constants.UserKindConstantsMixin),
        ),
        migrations.CreateModel(
            name='UserInvitation',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('uuid', django_extensions.db.fields.UUIDField(max_length=36, editable=False, blank=True)),
                ('expires_at', models.DateTimeField()),
                ('created', models.DateTimeField(auto_now_add=True)),
                ('receiver', models.ForeignKey(related_name=b'invitations', to=settings.AUTH_USER_MODEL)),
                ('sender', models.ForeignKey(related_name=b'invitations_sent', blank=True, to=settings.AUTH_USER_MODEL, null=True)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.AlterUniqueTogether(
            name='userinvitation',
            unique_together=set([('sender', 'receiver')]),
        ),
        migrations.AddField(
            model_name='user',
            name='invited_by',
            field=models.ManyToManyField(related_name=b'invited_users', through='users.UserInvitation', to=settings.AUTH_USER_MODEL),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='user',
            name='location',
            field=models.ForeignKey(to='locations.Location', null=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='user',
            name='roles',
            field=models.ManyToManyField(related_name=b'users', to='roles.Role'),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='user',
            name='skill_level',
            field=models.ForeignKey(to='categories.SkillLevel', null=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='user',
            name='user_permissions',
            field=models.ManyToManyField(help_text=b'Specific permissions for this user.', to='auth.Permission', verbose_name='user permissions', blank=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='user',
            name='vendor',
            field=models.ForeignKey(related_name=b'users', blank=True, to='vendors.Vendor', null=True),
            preserve_default=True,
        ),
    ]
