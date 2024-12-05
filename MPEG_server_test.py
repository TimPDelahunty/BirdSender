import io
import logging
import socketserver
from http import server
from threading import Condition

# Imports for the Picamera2 and MJPEG encoding functionality
from picamera2 import Picamera2
from picamera2.encoders import MJPEGEncoder
from picamera2.outputs import FileOutput

# HTML template for displaying the video stream
PAGE = """\
<html>
<head>
<title>picamera2 MJPEG streaming demo</title>
</head>
<body>
<h1>Picamera2 MJPEG Streaming Demo</h1>
<img src="stream.mjpg" width="640" height="480" />
</body>
</html>
"""

# Class to handle streaming output; acts as a buffer for frames
class StreamingOutput(io.BufferedIOBase):
    def __init__(self):
        self.frame = None
        self.condition = Condition()  # Condition variable for thread synchronization

    def write(self, buf):
        # When a new frame is written, notify all waiting threads
        with self.condition:
            self.frame = buf
            self.condition.notify_all()

# Class to handle HTTP requests for the video stream
class StreamingHandler(server.BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == '/':
            # Redirect to the index page
            self.send_response(301)
            self.send_header('Location', '/index.html')
            self.end_headers()
        elif self.path == '/index.html':
            # Serve the HTML page
            content = PAGE.encode('utf-8')
            self.send_response(200)
            self.send_header('Content-Type', 'text/html')
            self.send_header('Content-Length', len(content))
            self.end_headers()
            self.wfile.write(content)
        elif self.path == '/stream.mjpg':
            # Serve the MJPEG stream
            self.send_response(200)
            self.send_header('Age', 0)
            self.send_header('Cache-Control', 'no-cache, private')
            self.send_header('Pragma', 'no-cache')
            self.send_header('Content-Type', 'multipart/x-mixed-replace; boundary=FRAME')
            self.end_headers()
            try:
                while True:
                    with output.condition:
                        output.condition.wait()  # Wait for a new frame
                        frame = output.frame
                    self.wfile.write(b'--FRAME\r\n')
                    self.send_header('Content-Type', 'image/jpeg')
                    self.send_header('Content-Length', len(frame))
                    self.end_headers()
                    self.wfile.write(frame)
                    self.wfile.write(b'\r\n')
            except Exception as e:
                # Log disconnection and other errors
                logging.warning(
                    'Removed streaming client %s: %s',
                    self.client_address, str(e))
        else:
            # Handle 404 errors
            self.send_error(404)
            self.end_headers()

# HTTP server for handling streaming requests
class StreamingServer(socketserver.ThreadingMixIn, server.HTTPServer):
    allow_reuse_address = True
    daemon_threads = True

# Initialize the camera
picam2 = Picamera2()
picam2.configure(picam2.create_video_configuration(main={"size": (640, 480)}))
output = StreamingOutput()

# Start the camera recording, outputting MJPEG frames to the buffer
picam2.start_recording(MJPEGEncoder(), FileOutput(output))

try:
    # Set up the server to listen on port 8000
    address = ('', 8000)
    server = StreamingServer(address, StreamingHandler)
    server.serve_forever()  # Start handling requests
finally:
    # Stop recording when the server is shut down
    picam2.stop_recording()
