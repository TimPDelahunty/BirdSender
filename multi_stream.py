from picamera2 import Picamera2
from picamera2.encoders import H264Encoder
from picamera2.outputs import FileOutput, FfmpegOutput
import time

#config the camera
picam2 = Picamera2()
video_config = picam2.create_video_configuration()
picam2.configure(video_config)
#set encoders
encoder = H264Encoder(repeat=True, iperiod=15)
#set outputs
output1 = FileOutput() #FfmpegOutput("-f mpegts udp://<ip-address>:12345") #stream to socket
#output2 = FileOutput() #send to output file
output2 = FfmpegOutput("testing78.mp4")
encoder.output = [output1, output2]
# Start streaming to the network.
picam2.start_encoder(encoder)
picam2.start(show_preview=True)
time.sleep(5)
# Start recording to a file.
#output2.fileoutput = "test7.h264"
output2.start()
time.sleep(5)
output2.stop()
# The file is closed, but carry on streaming to the network.
time.sleep(9999999)