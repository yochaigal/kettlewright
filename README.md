# Kettlewright Setup

1. Create a directory for environment variables and the SQLite database:
   
       mkdir -p ~/docker/kettlewright/instance

2. Copy `.env.template` to the directory and rename it to `.env`:
   
       cp [repo_directory]/.env.template ~/docker/kettlewright/.env

3. Edit `.env` with appropriate values.

4. Pull the Docker image:
   
       docker pull yochaigal/kettlewright

5. Create the database:
   
       docker run -it --env-file .env -e UID=$(id -u) -e GID=$(id -g) -v $(pwd)/instance:/app/instance yochaigal/kettlewright /bin/sh -c "flask db upgrade"

6. Start Kettlewright:
   
       docker run --env-file .env -e UID=$(id -u) -e GID=$(id -g) -v $(pwd)/instance:/app/instance -p 8000:8000 --restart always yochaigal/kettlewright

7. Open http://127.0.0.1:8000 to access Kettlewright. You can stop the application with `Ctrl+C` in the terminal.

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

First, stop the container:

       docker stop [container]

Then remove it:

       docker rm [container]

Pull the latest image:

       docker pull yochaigal/kettlewright

Start a new container using the latest image:

       docker run --env-file .env -e UID=$(id -u) -e GID=$(id -g) -v $(pwd)/instance:/app/instance -p 8000:8000 --restart always yochaigal/kettlewright

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
