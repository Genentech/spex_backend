FROM python:3.9.2

# Keeps Python from generating .pyc files in the container
ENV PYTHONDONTWRITEBYTECODE = 1 \
    # Turns off buffering for easier container logging
    PYTHONUNBUFFERED = 1

WORKDIR /app
COPY . /app

RUN pip install pipenv && pipenv install --system --deploy --ignore-pipfile

EXPOSE 8080
CMD ["python", "app.py"]
