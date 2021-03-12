# For more information, please refer to https://aka.ms/vscode-docker-python
FROM python:3.9.2
USER root

# Keeps Python from generating .pyc files in the container
ENV PYTHONDONTWRITEBYTECODE=1

# Turns off buffering for easier container logging
ENV PYTHONUNBUFFERED=1
ARG CORS_HEADERS=Content-Type
ENV CORS_HEADERS=$CORS_HEADERS

ARG CORS_METHODS=GET,POST,OPTIONS
ENV CORS_METHODS=$CORS_METHODS

ARG ARANGODB_DATABASE_NAME=genentechdb
ENV ARANGODB_DATABASE_NAME=$ARANGODB_DATABASE_NAME

ARG ARANGODB_DATABASE_URL='http://host.docker.internal:8529'
ENV ARANGODB_DATABASE_URL=$ARANGODB_DATABASE_URL

ARG ARANGODB_USERNAME=root
ENV ARANGODB_USERNAME=$ARANGODB_USERNAME

ARG ARANGODB_PASSWORD=pass
ENV ARANGODB_PASSWORD=$ARANGODB_PASSWORD

ARG OMERO_HOST=localhost
ENV OMERO_HOST=$OMERO_HOST

ARG OMERO_PROXY_PATH='http://host.docker.internal:4080'
ENV OMERO_PROXY_PATH=$OMERO_PROXY_PATH

ARG JWT_SECRET_KEY=qmS58HtptborFt-5gA1icN4gOTDSm_P9mUiVjmheCfmQSCFig6vnKKvzXU_1hABx
ENV JWT_SECRET_KEY=$JWT_SECRET_KEY

# Install pip requirements
# COPY requirements.txt .
WORKDIR /app
COPY . /app
# RUN python -m pip install -r requirements.txt



# RUN pwd
# RUN python ./python-arango/setup.py install
RUN pip install pipenv && pipenv install --system --deploy --ignore-pipfile
RUN git clone https://github.com/joowani/python-arango.git
RUN cd python-arango && python setup.py install

WORKDIR /app
COPY . /app

# Switching to a non-root user, please refer to https://aka.ms/vscode-docker-python-user-rights
# RUN useradd appuser && chown -R appuser /app
# USER appuser

EXPOSE 8080
CMD ["python", "app.py"]
