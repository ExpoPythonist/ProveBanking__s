from optparse import make_option

from django.db import connection
from django.core.management import (call_command, get_commands,
                                    load_command_class)
from django.core.management import BaseCommand

from tenant_schemas.utils import get_tenant_model, get_public_schema_name


class Command(BaseCommand):
    help = 'Wrapper to run django commands on all tenants'

    def __init__(self, *args, **kwargs):
        super(Command, self).__init__(*args, **kwargs)
        self.option_list += (
            make_option("-p", "--skip-public", dest="skip_public",
                        action="store_true", default=False),
            make_option("--command-options", "--command-options", dest="command_options",
                        action="store", default=''),
        )

    def execute_command(self, tenant, command_name, *args, **options):
        verbosity = int(options.get('verbosity'))

        if verbosity >= 1:
            print()
            print(self.style.NOTICE("=== Switching to schema '")
                  + self.style.SQL_TABLE(tenant.schema_name)
                  + self.style.NOTICE("' then calling %s:" % command_name))

        connection.set_tenant(tenant)

        cmd_opts = options.pop('command_options', '')
        for opt in cmd_opts.split(' '):
            if '=' in opt:
                key, value = opt.split('=')
                options[key] = value
        call_command(command_name, *args, **options)

    def handle(self, *args, **options):
        """
        Iterates a command over all registered schemata.
        """
        for tenant in get_tenant_model().objects.all():
            if not (options.pop('skip_public', None) and
                    tenant.schema_name == get_public_schema_name()):
                self.execute_command(tenant, args[0], *args[1:], **options)
