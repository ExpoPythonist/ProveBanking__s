#!/usr/bin/env python
import os
import sys

import eventlet
import eventlet.debug


os.environ["EVENTLET_NOPATCH"] = 'True'
eventlet.monkey_patch()
eventlet.monkey_patch(psycopg=True)
eventlet.debug.hub_prevent_multiple_readers(False)

if __name__ == "__main__":
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "med_social.settings")

    from django.core.management import execute_from_command_line
    from med_social import patches
    patches.apply()
    execute_from_command_line(sys.argv)
