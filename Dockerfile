FROM python:3.10
ENV PYTHONUNBUFFERED=1
WORKDIR /app
COPY requirements.txt /app/
RUN pip install --no-cache-dir -r /app/requirements.txt
COPY . /app/

ARG UID=1000
ARG GID=1000
RUN groupadd -g $GID kettlewright && \
    useradd -m -u $UID -g $GID kettlewright && \
    chown -R kettlewright:kettlewright /app

USER kettlewright
EXPOSE 8000
CMD ["/bin/sh", "-c", "flask db upgrade && gunicorn --worker-class eventlet -w 2 -b 0.0.0.0:8000 app:application"]
