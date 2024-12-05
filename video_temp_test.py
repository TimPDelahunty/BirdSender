import io
import logging
import socketserver
from http import server
from multiprocessing import Process
from threading import Condition  # Add this import
import requests
import os
import tempfile
import time
from datetime import datetime
from picamera2 import Picamera2
from picamera2.encoders import MJPEGEncoder, H264Encoder
from picamera2.outputs import FileOutput



encoder = H264Encoder(10000000)
picam2 = Picamera2()
config = picam2.configure(picam2.create_video_configuration())

#picam2 = Picamera2()
picam2.start(show_preview = True)
while True:
    with tempfile.NamedTemporaryFile(delete=False, suffix='.h264') as temp_file:
        video_name = temp_file.name
        print(f"Recording to temporary file: {video_name}")
        picam2.start_encoder(encoder, video_name)
        time.sleep(5)  # Record for 5 seconds
        picam2.stop_encoder()
        print("Recording finished. Sending video.")
        #send_video_to_server(video_name, "http://192.168.0.205:5000/upload")
        #os.remove(video_name)
        print(f"Temporary video file {video_name} removed.")
    time.sleep(10)  # Wait before next recording to avoid constant uploads