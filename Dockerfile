FROM resin/raspberrypi2-debian:jessie
# FROM debian:jessie

RUN export DEBIAN_FRONTEND=noninteractive; apt-get update && apt-get install -y --force-yes python-flask python-serial python-dev libraspberrypi-bin python-pip
RUN pip install picamera

ADD /app /app
ADD /start.sh /app/start.sh

EXPOSE 80
CMD ["bash", "/app/start.sh"]
