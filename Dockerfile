FROM python:3.9.5

ARG TOKEN

RUN mkdir -p /usr/src/asap_feedback

WORKDIR /usr/src/asap_feedback

COPY ./requirements.txt /usr/src/asap_feedback
RUN pip install --no-cache-dir -r requirements.txt
COPY . /usr/src/asap_feedback

CMD python main.py $TOKEN
