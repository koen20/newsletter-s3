FROM python:3.11-slim

COPY ./requirements.txt /requirements.txt

RUN pip3 install --no-cache-dir -r /requirements.txt && pip3 install gunicorn
WORKDIR /src
COPY ./ /src
CMD [ "gunicorn", "-b" , "0.0.0.0:8080", "app:app"]