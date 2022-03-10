import os
from fabric.api import *
from fabric.contrib.console import confirm
from fabric.contrib import files

#import logging; logging.basicConfig(level=logging.DEBUG)

# Default config
env.user = 'www-data'
env.hosts = ['localhost']
env.git_branch = 'staging'
env.git_repo = 'ssh://git@bitbucket.org/opinr/thevetted.git'
env.project_root = '/src/thevetted/VPP/'
env.app_root = '/src/thevetted/VPP/med_social'
env.use_ssh_config = True

# Per server config
def prod():
    env.user = 'www-data'
    env.hosts = ['54.160.240.199']
    env.git_branch = 'production'
    env.host_config = os.path.join(env.app_root, 'deploy/hosts/prod/')

def staging():
    env.user = 'www-data'
    env.hosts = ['54.221.251.144'],
    env.git_branch = 'staging'
    env.project_root = '/mnt/staging.thevetted.net/thevetted/'
    env.app_root = '/mnt/staging.thevetted.net/thevetted/med_social'
    env.host_config = os.path.join(env.app_root, 'deploy/staging/prod/')

def test():
    env.user = 'www-data'
    env.hosts = ['54.251.250.223']
    env.git_branch = 'staging'


def vagrant():
    env.user = 'www-data'
    env.hosts = ['192.168.33.10']
    env.git_branch = 'staging'


# Utils
def ve(fab_command, command, exec_path='ve/bin/python'):
    fab_command('%s %s' % (os.path.join(env.project_root, exec_path), command))


# Tasks
def clean_pyc_files():
    with cd(env.app_root):
        run('find . -name "*.pyc" -exec rm -rf {} \\;')


def update_code():
    with cd(env.project_root):
        run('git fetch origin')  # in case branch does not exist locally at first run
        run('git reset --hard HEAD')
        run('git checkout %s' % env.git_branch)
        run('git pull origin %s' % env.git_branch)


def reset_git_branch():
    with cd(env.project_root):
        run('git checkout master')
        run('git branch -D %s' % env.git_branch)
        run('git pull')
        run('git checkout origin/%s' % env.git_branch)
        run('git checkout -b %s' % env.git_branch)
        run('git pull origin %s' % env.git_branch)

def migrate_db():
    execute(sync_shared)
    execute(sync_tenants)


def add_postgres_functions():
    ve(run, 'manage.py dbshell < deploy/sql/postgres_functions.sql')


def sync_shared():
    with cd(env.project_root):
        #ve(run, 'manage.py sync_schemas --shared')
        ve(run, 'manage.py migrate_schemas --shared')


def sync_tenants():
    with cd(env.project_root):
        #ve(run, 'manage.py sync_schemas --tenant')
        ve(run, 'manage.py migrate_schemas --tenant')


def pip_requirements():
    with cd(env.project_root):
        ve(run, 'install -r requirements.txt', exec_path='ve/bin/pip')


def collectstatic():
    with cd(env.project_root):
        ve(run, 'manage.py collectstatic --noinput')


def install_django_watson():
    with cd(env.project_root):
        ve(run, 'manage.py tenant_installwatson')


def build_django_watson():
    with cd(env.project_root):
        ve(run, 'manage.py tenant_buildwatson')


def backup_databases():
    with cd(env.project_root):
        ve(run, 'manage.py backup_databases')


def clean_static():
    run('rm -r %s' % os.path.join(env.project_root, 'med_social/static_collected'))


def __restart_pid__(pidfile, force_method=None):
    if files.exists(pidfile):
        try:
            pid = int(run('cat %s' % pidfile))
            sudo('kill -HUP %d' % pid)
            return
        except Exception, e:
            print e

    if force_method and confirm('Graceful restart failed! Full restart instead?', False):
        execute(force_method)


def status_all():
    with cd(env.project_root):
        ve(run, 've/bin/circusctl status')


def restart_webapp():
    with cd(env.project_root):
        ve(run, 've/bin/circusctl restart webapp')


def reload_webapp():
    with cd(env.project_root):
        ve(run, 've/bin/circusctl reload webapp')


def stop_webapp():
    with cd(env.project_root):
        ve(run, 've/bin/circusctl stop webapp')


def restart_celery():
    with cd(env.project_root):
        ve(run, 've/bin/circusctl restart celeryd')


def reload_celery():
    with cd(env.project_root):
        ve(run, 've/bin/circusctl reload celeryd')


def stop_celery():
    with cd(env.project_root):
        ve(run, 've/bin/circusctl stop celeryd')


def restart_celerybeat():
    with cd(env.project_root):
        ve(run, 've/bin/circusctl restart celerybeat')


def reload_celerybeat():
    with cd(env.project_root):
        ve(run, 've/bin/circusctl reload celerybeat')


def stop_celerybeat():
    with cd(env.project_root):
        ve(run, 've/bin/circusctl stop celerybeat')


def restart_all():
    with cd(env.project_root):
        ve(run, 've/bin/circusctl restart')


def reload_all():
    with cd(env.project_root):
        ve(run, 've/bin/circusctl reload')


def clean_content_types():
    with cd(env.project_root):
        ve(run, 'manage.py tenant_comamnd clean_content_types')


def update_site_names():
    with cd(env.project_root):
        ve(run, 'manage.py tenant_update_sitenames')


def deploy():
    execute(update_code)
    execute(migrate_db)
    execute(collectstatic)
    execute(reload_all)
