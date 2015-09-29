from flask import Flask, render_template
import logging
from gps import SerialGPS
from camera import Camera

# Disable Flask logging...
log = logging.getLogger('werkzeug')
log.setLevel(logging.ERROR)

app = Flask(__name__)

gps = SerialGPS()
c = Camera()


@app.route('/')
def index():
    return render_template('index.html', location=gps.json())


@app.route('/gps')
def gps_info():
    return gps.json()


@app.route('/camera')
def camera_base64():
    return c.base64_img


if __name__ == '__main__':
    gps.start()
    c.start()
    app.run(host='0.0.0.0', port=80)
    gps.stop()
    c.stop()
