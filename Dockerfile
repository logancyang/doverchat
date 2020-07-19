FROM python:3.6.11-slim

COPY ./requirements.txt /application/requirements.txt
WORKDIR /application

RUN pip install -r requirements.txt
COPY . /application

EXPOSE 8100
CMD ["gunicorn", "--worker-class", "eventlet", "-w", "1", "-t", "99999",\
"--max-requests", "1200", "-b", "0.0.0.0:8100", "application:app"]
