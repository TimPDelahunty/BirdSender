import io
import logging
import socketserver
from http import server
from threading import Condition, Thread
import requests
import os
import tempfile
import time
from datetime import datetime
from picamera2 import Picamera2
from picamera2.encoders import MJPEGEncoder, H264Encoder
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
        print("Frame received and written to buffer")  # Debug statement

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
                logging.warning('Removed streaming client %s: %s', self.client_address, str(e))
        else:
            # Handle 404 errors
            self.send_error(404)
            self.end_headers()

# HTTP server for handling streaming requests
class StreamingServer(socketserver.ThreadingMixIn, server.HTTPServer):
    allow_reuse_address = True
    daemon_threads = True

# Function to send recorded video to receiving server
def send_video_to_server(video_file_path, receiving_pi_url):
    files = {'video': open(video_file_path, 'rb')}
    try:
        response = requests.post(receiving_pi_url, files=files)
        if response.status_code == 200:
            print(f"Video {video_file_path} sent successfully.")
        else:
            print(f"Failed to send video: {response.status_code} {response.text}")
    except requests.exceptions.RequestException as e:
        print(f"Error while sending video: {str(e)}")
    finally:
        files['video'].close()

# Function to record video and send to the receiving Pi
def record_and_send_video():
    encoder = H264Encoder(10000000)
    while True:
        with tempfile.NamedTemporaryFile(delete=False, suffix='.h264') as temp_file:
            video_name = temp_file.name
            print(f"Recording to temporary file: {video_name}")
            picam2.start_encoder(encoder, video_name)
            time.sleep(5)  # Record for 5 seconds
            picam2.stop_encoder()
            print("Recording finished. Sending video.")
            send_video_to_server(video_name, "http://192.168.0.205:5000/upload")
            os.remove(video_name)
            print(f"Temporary video file {video_name} removed.")
        time.sleep(10)  # Wait before next recording to avoid constant uploads

# Initialize the camera
picam2 = Picamera2()
picam2.configure(picam2.create_video_configuration(main={"size": (640, 480)}))
output = StreamingOutput()

# Start the camera recording, outputting MJPEG frames to the buffer
picam2.start_recording(MJPEGEncoder(), FileOutput(output))

# Start the server and video sending in separate threads
if __name__ == "__main__":
    # Start video sending in a separate thread
    video_thread = Thread(target=record_and_send_video)
    video_thread.start()

    # Start the MJPEG stream server
    try:
        address = ('', 8000)
        server = StreamingServer(address, StreamingHandler)
        print("Starting MJPEG stream server on port 8000...")
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        picam2.stop_recording()
        print("Server stopped.")
