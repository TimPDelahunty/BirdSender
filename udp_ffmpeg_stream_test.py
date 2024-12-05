from picamera2 import Picamera2
from picamera2.encoders import H264Encoder, MJPEGEncoder
from picamera2.outputs import FfmpegOutput

# Initialize Picamera2
picam2 = Picamera2()
picam2.configure(picam2.create_video_configuration())
picam2.start()

# Encoder setup with H.264 encoding
stream_encoder = H264Encoder(1000000)  # Adjust bitrate as needed

# Define FfmpegOutput with explicit format option for MPEG Transport Stream
output = FfmpegOutput("-f mpegts udp://192.168.0.205:8001")

# Start recording to the ffmpeg network stream
picam2.start_recording(stream_encoder, output)

# Keep the stream running until manually stopped
try:
    while True:
        pass
except KeyboardInterrupt:
    pass
finally:
    picam2.stop_recording()
