FROM python:3.9.5

ARG PORT

RUN mkdir -p /usr/src/cherry

WORKDIR /usr/src/cherry

COPY ./requirements.txt /usr/src/cherry
RUN pip install --no-cache-dir -r requirements.txt
COPY . /usr/src/cherry
EXPOSE ${PORT}

CMD uvicorn main:app --reload --port ${PORT} --host 0.0.0.0
