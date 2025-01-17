FROM python:3.11-buster

ENV WORKDIR_PATH /app

WORKDIR $WORKDIR_PATH
RUN apt-get update -y && apt-get install vim -y && pip install pipenv

COPY ./Pipfile* .
RUN pipenv install --deploy --system --clear

COPY --chmod=0444 . .
RUN find $WORKDIR_PATH -type d -exec chown $USER_CONTAINER:$USER_CONTAINER {} \;
RUN find $WORKDIR_PATH -type d -exec chmod 755 {} \;

USER $USER_CONTAINER
CMD python main.py
