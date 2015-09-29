import io
import time
import base64
import threading
import picamera


class Camera(threading.Thread):
    _stop = threading.Event()
    base64_img = 'data:image/jpg;base64,'

    def run(self):
        with picamera.PiCamera() as c:
            c.resolution = (320, 240)
            c.start_preview()
            time.sleep(2)

            while not self._stop.is_set():
                stream = io.BytesIO()
                c.capture(stream, 'jpeg')
                self.base64_img = 'data:image/jpg;base64,%s' % (base64.encodestring(stream.getvalue()))
                time.sleep(1)

            c.stop_preview()

    def stop(self):
        self._stop.set()
