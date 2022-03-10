from optparse import make_option

from django.core.management.base import BaseCommand
from django.db import connection


class Command(BaseCommand):
    help = "Drop the tables."
    FIND_TABLES_QUERY = "select table_name from information_schema.tables where table_schema = '{}' and table_name LIKE '{}';"
    DROP_TABLES_QUERY= "DROP TABLE {} cascade;"

    def handle(self, *args, **options):
        table_name = args[0]
        cur = connection.cursor()
        cur.execute(self.FIND_TABLES_QUERY.format(connection.get_schema(), table_name))
        tables = cur.fetchall()
        if tables:
            print('Dropping {}'.format('\n'.join([T[0] for T in tables])))
            #cur.execute(self.DROP_TABLES_QUERY.format(','.join([T[0] for T in tables])))
            print('Done :)')
        else:
            print('No tables to drop')
