import io
import time
import base64
import threading
import picamera


class Camera(threading.Thread):
    _stop = threading.Event()
    stream = io.BytesIO()

    def run(self):
        with picamera.PiCamera() as c:
            c.start_preview()
            time.sleep(2)

            while not self._stop.is_set():
                c.capture(self.stream, 'jpeg')
                time.sleep(1)

            c.stop_preview()

    def stop(self):
        self._stop.set()

    def get_image(self):
        return self.stream.getvalue()

    def get_base64(self):
        return 'data:image/jpg;base64,%s' % (base64.encodestring(self.get_image()))
