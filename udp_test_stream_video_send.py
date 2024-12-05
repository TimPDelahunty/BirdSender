from picamera2 import Picamera2
from picamera2.encoders import H264Encoder, Quality
from picamera2.outputs import FileOutput, FfmpegOutput
import time
import os
from datetime import datetime
from multiprocessing import Process
import requests


#integrate this into detect bird. this file streams and recrods and also sends the reocridng

# Record and transfer videos function
def transfer_video(video_name):
    target_device = "http://192.168.0.205:5000/upload"  # Receiving Pi upload endpoint
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


# Initialize Picamera2 and video configurations
picam2 = Picamera2()
video_config = picam2.create_video_configuration(main={"size": (640, 480)})  # keep at this resolution for streaming
picam2.configure(video_config)

encoder = H264Encoder(repeat=True, iperiod=120)
output1 = FfmpegOutput("-f mpegts udp://192.168.0.205:8001")
output2 = FileOutput()
encoder.output = [output1, output2]

# Main function to run both live stream and file transfer concurrently
if __name__ == "__main__":
    picam2.start_encoder(encoder, quality=Quality.VERY_LOW)
    picam2.start()
    increment = 0

    while True:
        print("Starting live stream...")
        increment = increment + 1
        time.sleep(5)
        print("finished sleeping")

        video_name = f"tester{increment}.h264"
        output2.fileoutput = video_name
        output2.start()
        time.sleep(5)
        output2.stop()

        # Ensure the file exists before trying to upload
        if os.path.exists(video_name):
            print(f"File {video_name} found, starting upload process...")
            transfer_process = Process(target=transfer_video, args=(video_name,))
            print("Starting video transfer process...")
            transfer_process.start()
            transfer_process.join()  # Wait for the transfer to complete
            print("Process done")
        else:
            print(f"File {video_name} does not exist.")

        time.sleep(5)  # Add a delay before the next cycle
