from gps import SerialGPS
from flask import Flask, render_template
import logging

# Disable Flask logging...
log = logging.getLogger('werkzeug')
log.setLevel(logging.ERROR)

app = Flask(__name__)
gps = SerialGPS()


@app.route('/')
def index():
    return render_template('index.html', location=gps.json())


@app.route('/gps')
def gps_info():
    return gps.json()


if __name__ == '__main__':
    gps.start()
    app.run(host='0.0.0.0', port=80)
    gps.stop()
