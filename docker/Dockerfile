FROM python:3.7                   
LABEL maintainer L11
ENV PYTHONUNBUFFERED 1
COPY requirements.txt /L11/docker/
COPY packages/ /L11/packages/
RUN pip install -r /L11/docker/requirements.txt && pip install --no-index --find-links=/L11/packages/django-apscheduler/django-apscheduler-0.6.2.tar.gz django-apscheduler
WORKDIR /L11/sourcecode/backend/