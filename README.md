# Kettlewright Setup

1. Create a file in ~/docker/kettlewright/ called `.env` and populate it with the following:

       BASE_URL=http://127.0.0.1:8000
       SECRET_KEY=[unique string]
       SQLALCHEMY_DATABASE_URI=sqlite:///db.sqlite
       MAIL_SERVER=[enter mail server details]
       MAIL_PORT=[Probably 587]
       MAIL_USE_TLS=[Probably 1]
       MAIL_USERNAME=[enter email address]
       MAIL_PASSWORD=[enter email password]
       REQUIRE_SIGNUP_CODE=[True_or_False]
       SIGNUP_CODE=[only needed if previous statement is True]
       USE_REDIS=[True_or_False]
       REDIS_URL=redis://redis-server:6379/0

> Note: You will likely not need to mark USE_REDIS as 'True' unless you are planning to support hundreds of users. In that case please adjust the required worker count (typically 2 * CPU cores + 1). See "Using a redis server" below for more details.


1. Pull the Docker image:

       docker pull yochaigal/kettlewright

2. Start Kettlewright

       docker run -d --name kettlewright --env-file ~/docker/kettlewright/.env -v kettlewright_db:/app/instance -p 8000:8000 --restart always yochaigal/kettlewright

3. Open [http://127.0.0.1:8000](http://127.0.0.1:8000) to access Kettlewright.

## After Kettlewright Has Been Installed

By default the Kettlewright container should be labeled _kettlewright_, but it helps to know how to do the following anyway!
To find the container id (typically the most recent container):

       docker ps -a

Then start or stop the container with:

       docker start/stop [container/label]

To see the logs, run:

       docker logs -f [container/label]
       Ctrl+C to exit

To remove old containers:

       docker rm [container/label]

To copy the database from the container volume:

       docker cp [container/label]:/app/instance/db.sqlite .

## Updating Kettlewright Manually

1. First, stop the container:

       docker stop [container/label]

2. Then remove it:

       docker rm [container/label]

3. Pull the latest image:

       docker pull yochaigal/kettlewright

4. Start a new container using the latest image:

       docker run -d --name kettlewright --env-file ~/docker/kettlewright/.env -v kettlewright_db:/app/instance -p 8000:8000 --restart always yochaigal/kettlewright

## Automated Updates

1. To update the Docker image automatically, install Watchtower:

       docker pull containrrr/watchtower

2. Then, run the following command:

       docker run -d --name watchtower --restart always -v /var/run/docker.sock:/var/run/docker.sock -e TZ=America/New_York containrrr/watchtower --cleanup --schedule "*/5 * * * *"
       
This will run Watchtower every 5 minutes and automatically at boot. It will update all available Docker images unless explicitly stated, as well as clean up old images.

## Using a redis server

If you plan to launch Kettlewright with multiple workers, you _must_ use a redis server as a message queue.

1. Set the USE_REDIS value to True in your .env file. 

2. Install redis:

       docker pull redis

3. Run the redis container:

       docker run --name redis-server --restart unless-stopped -p 6379:6379 -d redis redis-server --save 60 1 --loglevel warning

4. Launch Kettlewright:

       docker run -d --name kettlewright --env-file ~/docker/kettlewright/.env -v kettlewright_db:/app/instance --link redis-server:redis-server -p 8000:8000 --restart always yochaigal/kettlewright

## Running the app without Docker (gunicorn)

1. Clone the repository.

2. Copy `.env.template` to `.env` and insert the appropriate values.

3. Create the python environment and lock it:

       pipenv shell
       pipenv lock

5. Install packages:

       pipenv sync

6. Initialize database:

       flask db upgrade
       exit

7. Run the app:

       pipenv run dotenv run -- gunicorn -k eventlet -w 1 -b 0.0.0.0:8000 --timeout 120 'app:application'

## Running the app without Docker (flask)

It can be helpful to run the app with flask, as you can see changes immediately rather than after restarting the server.

1. Add USE_FLASK=True to the .env file

2. Create the python environment and lock it:

       pipenv shell
       pipenv lock

3. Install packages:

       pipenv sync

4. Initialize database:

       flask db upgrade

5. Run the app:

       flask run --port=8000 --debug

## Attribution

- **David Stearns** -  Software Development, QA, Testing
- **Yochai Gal** - Project Design, DevOps, Documentation

### Tools

- **tlomdev's tokens** - A free, CC-BY-SA [token pack](https://tlomdev.itch.io/tlomdevs-tokens) by [tlomdev](https://tlomdev.itch.io/).
- **magick.css** - A classless [CSS framework](https://css.winterveil.net/) designed by [winterveil](https://github.com/wintermute-cell).
- **docker** - A platform for building and managing containerized applications. More on docker [here](https://www.docker.com/).
- **flask** -  A lightweight Python web framework for building web applications. More on flask [here](https://flask.palletsprojects.com/en/3.0.x/).
- **sqlite** - A fast, self-contained and full-featured SQL database engine. More on SQLite [here](https://www.sqlite.org/).
- **redis** - A real-time in-memory data structure store used as a database, cache, and message broker. More on redis [here](https://redis.io/).
