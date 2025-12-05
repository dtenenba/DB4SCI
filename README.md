## MyDB Containerzed Database Application Service 

MyDB is Python Flask application that creates and manages database containers.
MyDB uses Docker Swarm. The application and databases it starts are docker services.
Docker volumes are provied for each database instance, along with a Docker config for
startup.

MyDB has its own metadata database for keeping apllication state, and the state
of the containers that it has created.

MyDB uses AD auth. The Authorization code is a standalong module that could be
replaced by a different method.

MyDB uses AWS S3

### Install

   - Copy the mydb/mydb_config_example.py to mydb/mydb_config.py and configure
your environment. 

  - Put all your secrets in .env. A template is provide: env_example. Edit and 
save as `.env`
  - Create the docker sercets from the .env file. Execute the shell command: `dbaas_secrets.sh`
  - Populate the dbass.yml file `envsubst   < dbaas.yml  > dbaas_resolved.yml`

Build the Mydb container with ./build_dbaas.sh
The container needs to be taged and pushed a repo to be used by Docker Swarm
docker tag dbaas:2.0.1 fredhutch/dbaas:2.0.1
docker push fredhutch/dbaas:2.0.1
docker stack deploy --detach -c dbaas_resolved.yml mydb

docker exec -it $(docker ps -q -f "label=com.docker.swarm.service.name=mydb_dbaas") env | grep -i ADs
While debugging, a new image can be pushed the service:
 docker service update --force --image dbaas:2.0.1 mydb_dbaas



#### Programming Notes for DBaas
[Developer Notes](development.md)

### Application Logs
[Application Logs](LOGS.md)

### Restore Procedures
[Restore Procedures] (RESTORE.md)
[backup and restore](https://github.com/FredHutch/sc-howto-private/tree/main/DB4Sci)

