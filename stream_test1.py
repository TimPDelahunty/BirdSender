import os
import time
import logging
import threading
import http.server
import socketserver
from picamera2 import Picamera2
from picamera2.encoders import H264Encoder
from picamera2.outputs import FfmpegOutput

# Setup HLS directory for storing stream segments and playlist
HLS_DIRECTORY = "/tmp/hls_stream"
os.makedirs(HLS_DIRECTORY, exist_ok=True)

# Initialize Picamera2 for streaming with IMX500
picam2 = Picamera2()

# Set up FFmpeg HLS output
output = FfmpegOutput(
    f"-f hls -hls_time 4 -hls_list_size 5 -hls_flags delete_segments -hls_allow_cache 0 {HLS_DIRECTORY}/stream.m3u8"
)

# Configure the camera to capture video
picam2.configure(picam2.create_video_configuration())
encoder = H264Encoder()

# Function to start the HTTP server to serve HLS files
def start_http_server():
    # Change directory to the HLS directory where stream files are stored
    os.chdir(HLS_DIRECTORY)

    # Start HTTP server to serve HLS files
    PORT = 8080
    Handler = http.server.SimpleHTTPRequestHandler
    logging.basicConfig(level=logging.INFO)
    Handler.log_message = lambda self, format, *args: logging.info(format % args)

    with socketserver.TCPServer(("", PORT), Handler) as httpd:
        logging.info(f"Serving at port {PORT}")
        httpd.serve_forever()

# Function to start streaming the video to HLS
def start_streaming():
    # Start recording to the output stream
    picam2.start_recording(encoder, output)
    logging.info("Streaming video in HLS format...")

# Start the HTTP server in a separate thread
http_server_thread = threading.Thread(target=start_http_server)
http_server_thread.start()

# Start the video stream
start_streaming()

# Run the streaming until you decide to stop
try:
    while True:
        time.sleep(1)  # Keep the script running and streaming
except KeyboardInterrupt:
    logging.info("Stopping streaming...")
    picam2.stop_recording()  # Stop recording when done
    logging.info("Stream stopped.")
