FROM spex.common:latest

# Keeps Python from generating .pyc files in the container
ENV PYTHONDONTWRITEBYTECODE 1
# Turns off buffering for easier container logging
ENV PYTHONUNBUFFERED 1

COPY ./common /app/common
COPY ./backend /app/backend
WORKDIR /app/backend

RUN echo "[uwsgi]" > /app/uwsgi.ini
RUN echo "module = app" >> /app/uwsgi.ini
RUN echo "callable = application" >> /app/uwsgi.ini
RUN echo "processes = 5" >> /app/uwsgi.ini
RUN echo "threads = 5" >> /app/uwsgi.ini
RUN echo "master = true" >> /app/uwsgi.ini
RUN echo "chmod-socket = 664" >> /app/uwsgi.ini
RUN echo "vacuum = true" >> /app/uwsgi.ini
RUN echo "die-on-term = true" >> /app/uwsgi.ini
RUN echo "buffer-size = 65535" >> /app/uwsgi.ini

RUN pip install uwsgi
RUN pipenv install --system --deploy --ignore-pipfile
RUN pip install seaborn matplotlib==3.5.1 MarkupSafe==2.0.1 anndata==0.8.0

EXPOSE 8080
CMD uwsgi --ini /app/uwsgi.ini --socket 0.0.0.0:8080
