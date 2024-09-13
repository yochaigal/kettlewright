# Kettlewright Setup

1. Create a directory for environment variables and the SQLite database:
   
       mkdir -p ~/docker/kettlewright/instance

2. Create a file called `.env` and populate it with the following:

```
BASE_URL=http://127.0.0.1
SECRET_KEY=[unique database password]
SQLALCHEMY_DATABASE_URI=sqlite:///db.sqlite
MAIL_SERVER=[enter mail server details]
MAIL_PORT=[Probably 587]
MAIL_USE_TLS=[Probably 1]
MAIL_USERNAME=[enter email address]
MAIL_PASSWORD=[enter email password]
REQUIRE_SIGNUP_CODE=[True_or_False]
SIGNUP_CODE=[only needed if previous statement is True]
```

You can also copy `.env.template` from the repo and rename it to `.env`.

1. Edit `.env` with appropriate values.

2. Pull the Docker image:
   
       docker pull yochaigal/kettlewright

3. Create the database:
   
       docker run -it --env-file .env -e UID=$(id -u) -e GID=$(id -g) -v $(pwd)/instance:/app/instance yochaigal/kettlewright /bin/sh -c "flask db upgrade"

4. Start Kettlewright:
   
       docker run --env-file .env -e UID=$(id -u) -e GID=$(id -g) -v $(pwd)/instance:/app/instance -p 8000:8000 --restart always yochaigal/kettlewright

5. Open http://127.0.0.1:8000 to access Kettlewright. You can stop the application with `Ctrl+C` in the terminal.

## After Kettlewright Has Been Installed

To run Kettlewright again, first find the container id (typically the most recent container):

       docker ps -a

Then start the container with:

       docker start [container]

To see the logs, run:

       docker logs -f [container]

To remove old containers:

       docker rm [container] 

## Updating Kettlewright

1. First, stop the container:

       docker stop [container]

2. Then remove it:

       docker rm [container]

3. Pull the latest image:

       docker pull yochaigal/kettlewright

4. Start a new container using the latest image:

       docker run --env-file .env -e UID=$(id -u) -e GID=$(id -g) -v $(pwd)/instance:/app/instance -p 8000:8000 --restart always yochaigal/kettlewright

### Automated Updates

1. To update the docker image automatically, install Watchtower:

       git pull containerr/watchtower

2. Then, run the following command:

       docker run -d --name watchtower --restart always -v /var/run/docker.sock:/var/run/docker.sock -e TZ=America/New_York containrrr/watchtower --cleanup --schedule "*/5 * * * *"

This command will run Watchtower every 5 minutes as well as automatically at boot. It will update all available docker images unless explicitly stated, as well as cleanup old images. 

## Running the app without Docker

1. Pull the repository.

2. Copy .env.template to .env and insert the appropriate values.

3. Create the python environment:

       pipenv shell

4. Install packages:

       pipenv sync

5. Initialize database:

       flask db upgrade
       exit

6. Run the app:

       pipenv run dotenv run -- gunicorn -k eventlet -w 2 -b 0.0.0.0:8000 'app:application'
