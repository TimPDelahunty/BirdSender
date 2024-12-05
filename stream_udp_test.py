# echo-client.py
import socket
import time

from picamera2 import Picamera2
from picamera2.encoders import H264Encoder
from picamera2.outputs import FileOutput

picam2 = Picamera2()
video_config = picam2.create_video_configuration({"size": (1280, 720)})
picam2.configure(video_config)
encoder = H264Encoder(1000000)

#host IP adress
host = "196.168.0.205"
#Port to connect to
port = 10001

with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
    #sock.connect((host, port)) #
    #sock.bind(('0.0.0.0', 9999))
    stream = sock.makefile("wb")
    picam2.start_recording(encoder, FileOutput(stream))
    time.sleep(20000)
    picam2.stop_recording()
    s.sendall(b"finished recording")
