

Connect to `thevetteddb` as database admin. You should create database and user first:

```
$ createdb thevetteddb
$ createuser vetteduser
```

Grant database access to user:

```
thevetteddb=# grant all privileges on database thevetteddb to vetteduser;
thevetteddb=# grant create on database thevetteddb to vetteduser;
thevetteddb=# grant all on schema public to vetteduser;
thevetteddb=# grant all on all tables in schema public to vetteduser;
thevetteddb=# grant all on all sequences in schema public to vetteduser;
thevetteddb=# grant all on all functions in schema public to vetteduser;
```

Load data:
```
$ python manage.py loaddata email_templates
```

To run command on custom schema, use `tenant_command` with specified schema name, e.g.:
```
$ python manage.py tenant_command loaddata ida.json --schema=schemaname
```

How to deploy code:

```
$ git pull
$ python manage.py migrate_schemas # if there been changes to database
$ sudo service uwsgi restart; sudo service circus restart
```

## Build frontend

Currently, frontend broken into multiple pieces. New frontend code should be written with Webpack modules.


For building frontend on server, you should run:

```
$ npm run build
$ ./manage.py collectstatic --noinput
```

For development, you may use:
```
$ npm run watch
```
This command will rebuild webpack-part on every code change.

### Workflow

Every feature required new branch. After feature completed, you should open Pull Request into master with your fixes. After pull request accepted by reviewer, it could be merged into core.

This is recommended workflow and should be applied to all features, except hot-fixes (some major bug, which affect systems operability dramatically).

### Servers List
```
Dev: ssh -i path/to/provencompany.pem ubuntu@54.183.80.177
Prod: ssh -i path/to/provencompany.pem ubuntu@52.9.155.120
Commercial: ssh -i path/to/provencompany.pem ubuntu@commercialdrones.proven.cc
```