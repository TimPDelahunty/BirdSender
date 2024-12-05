import os
import time
from datetime import datetime
from multiprocessing import Process
import requests
from picamera2 import Picamera2
from picamera2.encoders import H264Encoder
from picamera2.outputs import FileOutput, FfmpegOutput

# Initialize Picamera2
picam2 = Picamera2()
encoder = H264Encoder(10000000)

# Live streaming function
    print("Starting live stream...")
    ffmpeg_output = FfmpegOutput("udp://192.168.0.205:8001", fmt="mpegts")
    picam2.start_encoder(encoder, ffmpeg_output)

def live_stream():
    #print("Starting live stream...")
   # ffmpeg_output = FfmpegOutput("udp://192.168.0.205:8001", fmt="mpegts")
    #picam2.start_encoder(encoder, ffmpeg_output)
    try:
        while True:
            time.sleep(1)  # Keep the stream running
    except KeyboardInterrupt:
        picam2.stop_encoder()
        print("Live stream stopped.")

# Record and transfer videos function
def record_and_transfer():
    target_device = "http://192.168.0.205:5000/upload"  # Receiving Pi upload endpoint
    num_birds_seen = 0

    while True:
        # Simulate bird detection
        time.sleep(5)  # Replace with your bird detection trigger
        print("Bird detected, starting recording...")

        # Record video
        dt = datetime.now()
        video_name = f"bird_capture_{dt.strftime('%Y%m%d_%H%M%S')}.h264"
        picam2.start_encoder(encoder, video_name)
        time.sleep(5)  # Record for 5 seconds
        picam2.stop_encoder()
        print(f"Recording {video_name} complete.")

        # Upload the video file
        print(f"Uploading {video_name} to the receiving Pi...")
        try:
            with open(video_name, 'rb') as f:
                files = {'file': (video_name, f)}
                response = requests.post(target_device, files=files)
            if response.status_code == 200:
                print(f"{video_name} uploaded successfully.")
            else:
                print(f"Failed to upload {video_name}: {response.status_code}")
        except Exception as e:
            print(f"Error uploading file: {e}")

        # Optional: Clean up local file after upload
        if os.path.exists(video_name):
            os.remove(video_name)
            print(f"Deleted local file: {video_name}")

# Main function to run both live stream and file transfer concurrently
if __name__ == "__main__":
    # Start live streaming in one process
    stream_process = Process(target=live_stream)

    # Start bird detection, recording, and transferring in another process
    transfer_process = Process(target=record_and_transfer)

    # Start both processes
    stream_process.start()
    transfer_process.start()

    # Wait for both processes to finish
    stream_process.join()
    transfer_process.join()
