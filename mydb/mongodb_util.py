import errno
import json
import os
import sys
import time

from jinja2 import Template
import pymongo
from pymongo import MongoClient

from . import (
    admin_db,
    mydb_config,
    swarm_util,
    touched,
)


def dbengine():
    return "MongoDB"


def auth_mongodb(dbuser, dbpass, port, dbname):
    connection_string = f"mongodb://{dbuser}:{dbpass}@{mydb_config.container_host}x:{port}/{dbname}"
    client = pymongo.MongoClient(connection_string)
    try:
        client.admin.command('ping')
    except (pymongo.errors.ConnectionFailure,
        pymongo.errors.OperationFailure) as e:
        print(f"Error connecting to MongoDB: {e}", file=sys.stderr)
        return False
    client.close()
    return True


def create_init_script(params):
    """Create admin roles and user account

    MongoDB initialization scripts in /docker-entrypoint-initdb.d/ are executed
    automatically when the container starts for the first time (when data directory is empty).
    """
    init_user_js = """// Create the user's database and user account
use '{{dbname}}';
db.collectionName.insertOne({ message: "Hello from MyDB", dbname: "{{dbname}}" });

// Create user with dbOwner role - full admin rights to this database
db.createUser({
    user: '{{dbuser}}',
    pwd: '{{dbuserpass}}',
    roles: [
        {role: 'dbOwner', db: '{{dbname}}'},
        {role: "dbAdmin", db: "admin" },
        {role: "userAdminAnyDatabase", db: "admin" } ]
});

"""
    template = Template(init_user_js)
    rendered_output = template.render(params)
    params["config_name"] = f"mydb_{params['Name']}_init_user.js"
    target_path = "/docker-entrypoint-initdb.d/init_user.js"
    return swarm_util.create_config(params, rendered_output, target_path)


def mongo_env(dbname):
    """Create MongoDB container environment

    Args:
        dbname: Database name for MONGO_INITDB_DATABASE
    """
    dbengine = "MongoDB"
    env = [
        f"MONGO_INITDB_ROOT_USERNAME={mydb_config.accounts[dbengine]['admin']}",
        f"MONGO_INITDB_ROOT_PASSWORD={mydb_config.accounts[dbengine]['admin_pass']}",
        f"MONGO_INITDB_DATABASE={dbname}",
        f"TZ={mydb_config.TZ}",
    ]
    return env


def build_params_mongo(info):
    """only used for migrate"""
    params = {}
    params["dbengine"] = info["dbengine"]
    params["dbname"] = info["dbname"]
    params["dbuser"] = info["dbuser"]
    params["dbuserpass"] = info["dbuserpass"]
    params["env"] = mongo_env(info["dbname"])
    return params


def create_mongodb(params):
    """Create MongoDB Service in Docker Swarm
    Called from mydb_views
    params is created from general_form UI
    """
    from .send_mail import send_mail

    dbengine = params["dbengine"]
    data = json.dumps(params, indent=4)
    print(f"DEBUG: mongodb_util.create_mongodb: params before: {data}")

    params["service_name"] = f"mydb_{params['Name']}"
    params["volume_name"] = f"mydb_{params['Name']}"

    # Check if service already exists
    if swarm_util.service_exists(params["service_name"]):
        return f"Service name {params['service_name']} already in use"

    # Create Docker volume
    volume_id, error = swarm_util.create_docker_volume(params["volume_name"])
    if error:
        return f"Error creating docker volume {params['volume_name']}. Error: {error}"

    # Create init script config
    config_ref = create_init_script(params)
    if config_ref is None:
        return "Error: creating Docker Config"

    # Get config data
    config_data = mydb_config.info[dbengine]
    params["mapped_db_vol"] = config_data["mapped_volume"]
    params["default_port"] = config_data["default_port"]
    params["service_user"] = config_data["service_user"]
    params["Port"] = admin_db.get_max_port()
    params["env"] = mongo_env(params["dbname"])

    # Create labels
    params["labels"] = {}
    for label in mydb_config.mydb_v1_meta_data:
        params["labels"][label] = params[label]
    params["labels"]["touched"] = touched.create_date_string()

    # Start the service
    service, error = swarm_util.start_service(params, config_ref)
    if service is None:
        return f"{error} {mydb_config.supportOrganization} has been notified"

    # Build response message
    res = "Your MongoDB database server has been created.\n\n"
    res += f'MongoDB URI: "mongodb://{params["dbuser"]}:{params["dbuserpass"]}@'
    res += f'{mydb_config.container_host}:{params["Port"]}/{params["dbname"]}"\n\n'
    res += "Use the mongo shell to connect:\n"
    connection = f"mongosh -u {params['dbuser']} --host {mydb_config.container_host} "
    connection += f"--port {params['Port']} "
    connection += f"--authenticationDatabase {params['dbname']} -p\n\n"
    print(f"DEBUG: mongodb_util: {connection}  password({params['dbuserpass']})")
    # Send notification email
    message = (
        f"MyDB created a new {dbengine} database called: {params['service_name']}\n"
    )
    message += f"Created by: {params['owner']} <{params['contact']}>\n"
    send_mail(f"MyDB: created {dbengine}", message, mydb_config.supportAdmin)

    return res + connection


def backup_mongodb(dbname, type, tag=None):
    (backupdir, backup_id) = container_util.create_backupdir(dbname)
    (c_id, dbengine) = admin_db.get_container_type(dbname)
    url = l = mydb_config.bucket + "/" + dbname + backupdir
    cmd = "mongodump --username %s " % mydb_config.accounts["MongoDB"]["admin"]
    cmd += "--password %s " % mydb_config.accounts["MongoDB"]["admin_pass"]
    cmd += "--out /var/backup" + backupdir  # OR --archive >filename
    admin_db.backup_log(
        c_id, dbname, "start", backup_id, type, url="", command=cmd, err_msg=""
    )
    result = container_util.exec_command(dbname, cmd)
    admin_db.backup_log(c_id, dbname, "end", backup_id, type, url, cmd, result)
    result = container_util.exec_command(dbname, cmd)
    admin_db.backup_log(c_id, dbname, "end", backup_id, type, url, cmd, result)
    admin_db.backup_log(c_id, dbname, "end", backup_id, type, url, cmd, result)
    return cmd, result
