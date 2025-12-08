#!/bin/bash

# Create secrets for MyDB
source .env
[[ ! -z "$AWS_BUCKET_NAME" ]] && echo -n "$AWS_BUCKET_NAME" | docker secret create mydb_aws_bucket_name -
[[ ! -z "$AWS_SECRET_ACCESS_KEY" ]] && echo -n "$AWS_SECRET_ACCESS_KEY" | docker secret create mydb_aws_access_key_id -
[[ ! -z "$AWS_SECRET_ACCESS_KEY" ]] && echo -n "$AWS_SECRET_ACCESS_KEY" | docker secret create mydb_aws_secret_access_key -
[[ ! -z "$FLASK_SECRET" ]] && echo -n "$FLASK_SECRET" | docker secret create mydb_flask_secret - 
[[ ! -z "$SQLALCHEMY_ADMIN_URI" ]] && echo -n "$SQLALCHEMY_ADMIN_URI"  | docker secret create mydb_sqlalchemy_admin_uri -
[[ ! -z "$SQLALCHEMY_MIGRATE_URI" ]] && echo -n "$SQLALCHEMY_MIGRATE_URI" | docker secret create mydb_sqlalchemy_migrate_uri -

