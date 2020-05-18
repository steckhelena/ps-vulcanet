FROM python:alpine3.6
COPY . /app
WORKDIR /app
RUN apk --update add \
      build-base
RUN pip install -r requirements.txt
EXPOSE 5678
CMD python ./queue_manager.py
