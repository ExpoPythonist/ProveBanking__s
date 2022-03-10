# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import projects.models
import med_social.libs.mixins
import django_hstore.fields
import autoslug.fields
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('categories', '0001_initial'),
        ('rates', '0001_initial'),
        ('vendors', '0002_auto_20140829_1150'),
        ('roles', '0001_initial'),
        ('locations', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='Project',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('status', models.PositiveSmallIntegerField(default=1, choices=[(1, b'Draft'), (2, b'Staffing'), (3, b'Staffed')])),
                ('title', models.CharField(max_length=255)),
                ('description', models.TextField(blank=True)),
                ('created', models.DateTimeField(auto_now_add=True)),
                ('modified', models.DateTimeField(auto_now=True)),
                ('ended', models.DateTimeField(null=True, blank=True)),
                ('budget', models.PositiveIntegerField(null=True)),
                ('start_date', models.DateField(null=True)),
                ('end_date', models.DateField(null=True)),
            ],
            options={
                'ordering': ('-modified',),
                'db_table': 'projects',
                'verbose_name': 'project',
                'verbose_name_plural': 'projects',
            },
            bases=(models.Model, med_social.libs.mixins.SerializableMixin),
        ),
        migrations.CreateModel(
            name='ProposedResource',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('final_rate', models.DecimalField(null=True, max_digits=10, decimal_places=0, blank=True)),
                ('allocation', models.PositiveSmallIntegerField(default=100, verbose_name='Allocation (%)')),
                ('start_date', models.DateField()),
                ('end_date', models.DateField()),
                ('status_changed_at', models.DateTimeField(null=True)),
                ('created', models.DateTimeField(auto_now_add=True)),
                ('modified', models.DateTimeField(auto_now=True)),
                ('changed_by', models.ForeignKey(related_name=b'edited_resources', to=settings.AUTH_USER_MODEL)),
                ('location', models.ForeignKey(to='locations.Location', null=True)),
                ('project', models.ForeignKey(related_name=b'proposals', to='projects.Project')),
                ('rate_card', models.ForeignKey(to='rates.Rate', null=True)),
            ],
            options={
                'ordering': ('-status__value',),
            },
            bases=(models.Model, projects.models.DurationMixin),
        ),
        migrations.CreateModel(
            name='ProposedResourceStatus',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(help_text=b'Unique name for the status', max_length=127)),
                ('vendor_name', models.CharField(default=b'', help_text=b'If other organizations should see a different name? Leave blank to use the same as above.', max_length=127, verbose_name='Organizations alias', blank=True)),
                ('slug', autoslug.fields.AutoSlugField(unique=True, editable=False)),
                ('value', models.PositiveSmallIntegerField(default=3, help_text=b'The state this status represents. This will help the system provide meaningful analytics to you and make smart decisions for you. <strong>Initiated</strong> can be set by vendors while proposing resources.', choices=[(3, b'Initiated'), (1, b'Cancelled'), (2, b'Failed'), (4, b'In progress'), (5, b'Success')])),
            ],
            options={
                'ordering': ('value',),
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='StaffingRequest',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('status', models.PositiveSmallIntegerField(default=1, choices=[(1, b'Draft'), (2, b'Staffing'), (3, b'Staffed')])),
                ('title', models.CharField(default=b'', max_length=127, blank=True)),
                ('kind', models.PositiveSmallIntegerField(default=1, choices=[(1, b'Staffing request'), (2, b'Fixed price projects')])),
                ('min_rate', models.DecimalField(null=True, max_digits=10, decimal_places=0, blank=True)),
                ('max_rate', models.DecimalField(null=True, max_digits=10, decimal_places=0, blank=True)),
                ('billing_period', models.PositiveSmallIntegerField(default=2, choices=[(1, b'Fixed'), (2, b'Hourly'), (3, b'Daily'), (4, b'Weekly')])),
                ('description', models.TextField(verbose_name='Summary', blank=True)),
                ('num_resources', models.PositiveSmallIntegerField(default=1, verbose_name='Number of people required')),
                ('allocation', models.PositiveSmallIntegerField(default=100, verbose_name='Allocation (%)')),
                ('start_date', models.DateField(null=True)),
                ('end_date', models.DateField(null=True)),
                ('is_public', models.BooleanField(default=True)),
                ('created', models.DateTimeField(auto_now_add=True)),
                ('modified', models.DateTimeField(auto_now=True)),
                ('document', models.FileField(null=True, upload_to=projects.models._get_document_upload_path)),
                ('meta', django_hstore.fields.DictionaryField(default={})),
                ('categories', models.ManyToManyField(related_name=b'staffing_requests', to='categories.Category')),
                ('created_by', models.ForeignKey(related_name=b'staffing_requests', to=settings.AUTH_USER_MODEL)),
                ('location', models.ForeignKey(related_name=b'staffing_requests', blank=True, to='locations.Location', null=True)),
                ('owners', models.ManyToManyField(related_name=b'owned_requests', to=settings.AUTH_USER_MODEL, blank=True)),
                ('people', models.ManyToManyField(related_name=b'visible_staffing_requests', to=settings.AUTH_USER_MODEL)),
                ('project', models.ForeignKey(related_name=b'staffing_requests', to='projects.Project')),
                ('proposed_staff', models.ManyToManyField(related_name=b'proposed_staffing_requests', to=settings.AUTH_USER_MODEL)),
                ('role', models.ForeignKey(to='roles.Role', null=True)),
                ('skill_level', models.ForeignKey(to='categories.SkillLevel', null=True)),
                ('vendors', models.ManyToManyField(related_name=b'visible_staffing_requests', to='vendors.Vendor')),
            ],
            options={
                'ordering': ('-modified',),
            },
            bases=(models.Model, med_social.libs.mixins.SerializableMixin, projects.models.DurationMixin),
        ),
        migrations.CreateModel(
            name='StaffingResponse',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('rate', models.DecimalField(null=True, max_digits=10, decimal_places=0, blank=True)),
                ('billing_period', models.PositiveSmallIntegerField(default=2, choices=[(1, b'Fixed'), (2, b'Hourly'), (3, b'Daily'), (4, b'Weekly')])),
                ('start_date', models.DateField(null=True)),
                ('end_date', models.DateField(null=True)),
                ('status', models.PositiveSmallIntegerField(default=1, choices=[(1, b'draft'), (2, b'sent')])),
                ('allocation', models.PositiveSmallIntegerField(default=100, verbose_name='Allocation (%)')),
                ('is_accepted', models.BooleanField(default=False)),
                ('created', models.DateTimeField(auto_now_add=True)),
                ('modified', models.DateTimeField(auto_now=True)),
                ('accepted_by', models.ForeignKey(related_name=b'accepted_responses', blank=True, to=settings.AUTH_USER_MODEL, null=True)),
                ('location', models.ForeignKey(to='locations.Location', null=True)),
                ('posted_by', models.ForeignKey(related_name=b'posted_responses', to=settings.AUTH_USER_MODEL)),
                ('request', models.ForeignKey(related_name=b'responses', to='projects.StaffingRequest')),
                ('role', models.ForeignKey(to='roles.Role', null=True)),
                ('vendor', models.ForeignKey(related_name=b'responses', to='vendors.Vendor', null=True)),
            ],
            options={
            },
            bases=(models.Model, med_social.libs.mixins.SerializableMixin, projects.models.DurationMixin),
        ),
        migrations.CreateModel(
            name='StatusFlow',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('driver', models.PositiveSmallIntegerField(default=1, help_text=b'Who can make this change', choices=[(1, b'Clients'), (2, b'Vendors'), (3, b'Everyone')])),
                ('backward', models.ForeignKey(related_name=b'forward_flows', to='projects.ProposedResourceStatus')),
                ('forward', models.ForeignKey(related_name=b'backward_flows', to='projects.ProposedResourceStatus')),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.AlterUniqueTogether(
            name='statusflow',
            unique_together=set([('backward', 'forward')]),
        ),
        migrations.AddField(
            model_name='proposedresourcestatus',
            name='forwards',
            field=models.ManyToManyField(help_text=b'Which status can this status change to', to='projects.ProposedResourceStatus', through='projects.StatusFlow'),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='proposedresource',
            name='request',
            field=models.ForeignKey(related_name=b'proposed', to='projects.StaffingRequest', null=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='proposedresource',
            name='resource',
            field=models.ForeignKey(related_name=b'proposed', to=settings.AUTH_USER_MODEL),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='proposedresource',
            name='role',
            field=models.ForeignKey(to='roles.Role', null=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='proposedresource',
            name='skill_level',
            field=models.ForeignKey(to='categories.SkillLevel', null=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='proposedresource',
            name='status',
            field=models.ForeignKey(related_name=b'proposed_resources', to='projects.ProposedResourceStatus', null=True),
            preserve_default=True,
        ),
        migrations.AlterUniqueTogether(
            name='proposedresource',
            unique_together=set([('project', 'resource', 'request', 'role', 'skill_level', 'location')]),
        ),
        migrations.AddField(
            model_name='project',
            name='staff',
            field=models.ManyToManyField(related_name=b'assigned_projects', through='projects.ProposedResource', to=settings.AUTH_USER_MODEL),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='project',
            name='user',
            field=models.ForeignKey(related_name=b'projects', to=settings.AUTH_USER_MODEL),
            preserve_default=True,
        ),
    ]
