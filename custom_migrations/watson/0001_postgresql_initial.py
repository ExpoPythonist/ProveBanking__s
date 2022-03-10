# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
from django.core.management import call_command


class Migration(migrations.Migration):

    dependencies = [
        ('contenttypes', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='SearchEntry',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('engine_slug', models.CharField(default='default', max_length=200, db_index=True)),
                ('object_id', models.TextField()),
                ('object_id_int', models.IntegerField(db_index=True, null=True, blank=True)),
                ('title', models.CharField(max_length=1000)),
                ('description', models.TextField(blank=True)),
                ('content', models.TextField(blank=True)),
                ('url', models.CharField(max_length=1000, blank=True)),
                ('meta_encoded', models.TextField()),
                ('content_type', models.ForeignKey(to='contenttypes.ContentType')),
            ],
            options={
                'verbose_name_plural': 'search entries',
            },
            bases=(models.Model,),
        ),
        migrations.RunSQL(
            """
            -- Create the search index.
            ALTER TABLE watson_searchentry ADD COLUMN search_tsv tsvector NOT NULL;
            CREATE INDEX watson_searchentry_search_tsv ON watson_searchentry USING gin(search_tsv);

            -- Create the trigger function.
            CREATE OR REPLACE FUNCTION watson_searchentry_trigger_handler() RETURNS trigger AS $$
            begin
                new.search_tsv :=
                    setweight(to_tsvector('pg_catalog.english', coalesce(new.title, '')), 'A') ||
                    setweight(to_tsvector('pg_catalog.english', coalesce(new.description, '')), 'C') ||
                    setweight(to_tsvector('pg_catalog.english', coalesce(new.content, '')), 'D');
                return new;
            end
            $$ LANGUAGE plpgsql;
            CREATE TRIGGER watson_searchentry_trigger BEFORE INSERT OR UPDATE
            ON watson_searchentry FOR EACH ROW EXECUTE PROCEDURE watson_searchentry_trigger_handler();
            """,
            """
            ALTER TABLE watson_searchentry DROP COLUMN search_tsv;

            DROP TRIGGER watson_searchentry_trigger ON watson_searchentry;

            DROP FUNCTION watson_searchentry_trigger_handler();
            """
        )
    ]
