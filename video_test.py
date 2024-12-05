import time

"""from picamera2 import Picamera2
from picamera2.encoders import H264Encoder
from picamera2.outputs import FfmpegOutput

picam2 = Picamera2()
video_config = picam2.create_video_configuration()
picam2.configure(video_config)

encoder = H264Encoder(10000000)
output = FfmpegOutput('test.mp4', audio=True)

picam2.start_and_record_video("test_puff.mp4", duration=8, show_preview = True)"""

from picamera2.encoders import H264Encoder, MJPEGEncoder#, FfmpegOutput
from picamera2.outputs import CircularOutput
from picamera2 import Picamera2

from picamera2 import CompletedRequest, MappedArray, Picamera2
from picamera2.devices import IMX500
from picamera2.devices.imx500 import NetworkIntrinsics
from picamera2.devices.imx500.postprocess import softmax






picam2 = Picamera2()
#picam2 = Picamera2()
config = picam2.configure(picam2.create_video_configuration())
encoder = H264Encoder(bitrate=10000000)

"""picam2.start(config, show_preview=True)
print("pausing for 3 seconds")
time.sleep(3)
print("DONE Sleeping")

picam2.start_and_record_video("test1.mp4", duration=5, show_preview = True)
print("thanks for watching")
picam2.stop()

picam2.start_encoder()"""



encoder1 = H264Encoder(10000000)
encoder2 = MJPEGEncoder(10000000)

picam2.start_encoder(encoder)
picam2.start(show_preview=True)

time.sleep(3)
print("time to record")
picam2.start_encoder(encoder1, 'test2.h264')
time.sleep(3)
picam2.stop_encoder(encoder1)
print("done recording")
time.sleep(3)
print("thanks")
picam2.stop()
picam2.stop_encoder()



"""

print("start recording")
picam2.start_recording(encoder, "testing_vid.mp4")
time.sleep(3)
picam2.stop_recording()
print("stopped recording")
time.sleep(5)
print("thanks for watching")
picam2.stop()"""