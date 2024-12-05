import argparse
import sys
from functools import lru_cache

import cv2
import numpy as np

from picamera2 import MappedArray, Picamera2
from picamera2.devices import IMX500
from picamera2.devices.imx500 import (NetworkIntrinsics,
                                      postprocess_nanodet_detection)

#recording stuff
from picamera2.encoders import H264Encoder, Quality
from picamera2.outputs import FileOutput, FfmpegOutput


import os
from multiprocessing import Process
import requests
import time
from datetime import datetime



last_detections = []
num_birds_seen = 0

class Detection:
    def __init__(self, coords, category, conf, metadata):
        """Create a Detection object, recording the bounding box, category and confidence."""
        self.category = category
        self.conf = conf
        self.box = imx500.convert_inference_coords(coords, metadata, picam2)


def parse_detections(metadata: dict):
    """Parse the output tensor into a number of detected objects, scaled to the ISP out."""
    global last_detections
    bbox_normalization = intrinsics.bbox_normalization
    threshold = args.threshold
    iou = args.iou
    max_detections = args.max_detections

    np_outputs = imx500.get_outputs(metadata, add_batch=True)
    input_w, input_h = imx500.get_input_size()
    if np_outputs is None:
        return last_detections
    if intrinsics.postprocess == "nanodet":
        boxes, scores, classes = \
            postprocess_nanodet_detection(outputs=np_outputs[0], conf=threshold, iou_thres=iou,
                                          max_out_dets=max_detections)[0]
        from picamera2.devices.imx500.postprocess import scale_boxes
        boxes = scale_boxes(boxes, 1, 1, input_h, input_w, False, False)
    else:
        boxes, scores, classes = np_outputs[0][0], np_outputs[1][0], np_outputs[2][0]
        if bbox_normalization:
            boxes = boxes / input_h

        boxes = np.array_split(boxes, 4, axis=1)
        boxes = zip(*boxes)

    last_detections = [
        Detection(box, category, score, metadata)
        for box, score, category in zip(boxes, scores, classes)
        if score > threshold
    ]

    return last_detections


@lru_cache
def get_labels():
    labels = intrinsics.labels

    if intrinsics.ignore_dash_labels:
        labels = [label for label in labels if label and label != "-"]

        
    return labels


def draw_detections(request, stream="main"):
    """Draw the detections for this request onto the ISP output."""
    detections = last_results
    if detections is None:
        return
    labels = get_labels()
    with MappedArray(request, stream) as m:



        for detection in detections:
            x, y, w, h = detection.box
            label = f"{labels[int(detection.category)]} ({detection.conf:.2f})"
            # Calculate text size and position
            (text_width, text_height), baseline = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.5, 1)
            text_x = x + 5
            text_y = y + 15

            # Create a copy of the array to draw the background with opacity
            overlay = m.array.copy()

            # Draw the background rectangle on the overlay
            cv2.rectangle(overlay,
                          (text_x, text_y - text_height),
                          (text_x + text_width, text_y + baseline),
                          (255, 255, 255),  # Background color (white)
                          cv2.FILLED)

            alpha = 0.30
            cv2.addWeighted(overlay, alpha, m.array, 1 - alpha, 0, m.array)

            # Draw text on top of the background
            cv2.putText(m.array, label, (text_x, text_y),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 255), 1)

            # Draw detection box
            cv2.rectangle(m.array, (x, y), (x + w, y + h), (0, 255, 0, 0), thickness=2)

        if intrinsics.preserve_aspect_ratio:
            b_x, b_y, b_w, b_h = imx500.get_roi_scaled(request)
            color = (255, 0, 0)  # red
            cv2.putText(m.array, "ROI", (b_x + 5, b_y + 15), cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 1)
            cv2.rectangle(m.array, (b_x, b_y), (b_x + b_w, b_y + b_h), (255, 0, 0, 0))

#record th birds and change camera for video capture
#Passed an encoder to record the video. video recorded in h264 format
#returns a timestamp of when the video was recorded
def record_bird(output2):
    global num_birds_seen

    #encoder = H264Encoder(10000000)
    # Getting the current date and time
    dt = datetime.now()
    video_name = f"bird_capture{num_birds_seen}.h264"
    num_birds_seen = num_birds_seen + 1  

    #print("time to record")
    #picam2.start_encoder(bird_encoder, video_name)
    #time.sleep(5)
    #picam2.stop_encoder(bird_encoder)
    #print("done recording")

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

    return (dt)

# transfer videos function via a post. executed as a multiple process
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





def get_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("--model", type=str, help="Path of the model",
                        default="/usr/share/imx500-models/imx500_network_ssd_mobilenetv2_fpnlite_320x320_pp.rpk")
    parser.add_argument("--fps", type=int, help="Frames per second")
    parser.add_argument("--bbox-normalization", action=argparse.BooleanOptionalAction, help="Normalize bbox")
    parser.add_argument("--threshold", type=float, default=0.55, help="Detection threshold")
    parser.add_argument("--iou", type=float, default=0.65, help="Set iou threshold")
    parser.add_argument("--max-detections", type=int, default=10, help="Set max detections")
    parser.add_argument("--ignore-dash-labels", action=argparse.BooleanOptionalAction, help="Remove '-' labels ")
    parser.add_argument("--postprocess", choices=["", "nanodet"],
                        default=None, help="Run post process of type")
    parser.add_argument("-r", "--preserve-aspect-ratio", action=argparse.BooleanOptionalAction,
                        help="preserve the pixel aspect ratio of the input tensor")
    parser.add_argument("--labels", type=str,
                        help="Path to the labels file")
    parser.add_argument("--print-intrinsics", action="store_true",
                        help="Print JSON network_intrinsics then exit")
    return parser.parse_args()


if __name__ == "__main__":
    args = get_args()

    # This must be called before instantiation of Picamera2
    imx500 = IMX500(args.model)
    intrinsics = imx500.network_intrinsics
    if not intrinsics:
        intrinsics = NetworkIntrinsics()
        intrinsics.task = "object detection"
    elif intrinsics.task != "object detection":
        print("Network is not an object detection task", file=sys.stderr)
        exit()

    # Override intrinsics from args
    for key, value in vars(args).items():
        if key == 'labels' and value is not None:
            with open(value, 'r') as f:
                intrinsics.labels = f.read().splitlines()
        elif hasattr(intrinsics, key) and value is not None:
            setattr(intrinsics, key, value)

    # Defaults
    if intrinsics.labels is None:
        with open("assets/coco_labels.txt", "r") as f:
            intrinsics.labels = f.read().splitlines()
    intrinsics.update_with_defaults()

    if args.print_intrinsics:
        print(intrinsics)
        exit()


    #init the camera
    picam2 = Picamera2(imx500.camera_num)
    #show the uploading
    imx500.show_network_fw_progress_bar()

    #configure cam
    video_config = picam2.create_video_configuration(main={"size": (640, 480)})  # keep at this resolution for streaming
    picam2.configure(video_config)

    #create the encoders

    encoder = H264Encoder(repeat=True, iperiod=120)
    #this output is the adress of the udp stream to go to
    output1 = FfmpegOutput("-f mpegts udp://192.168.0.205:8001")
    #this output creates the output file to save video to
    output2 = FileOutput()
    #give the encoder the outputs
    encoder.output = [output1, output2]

    #start the camera
    picam2.start_encoder(encoder)
    
    picam2.start(show_preview=True)
    print("Starting live stream...")

    if intrinsics.preserve_aspect_ratio:
        imx500.set_auto_aspect_ratio()

    last_results = None
    picam2.pre_callback = draw_detections


    while True:
        last_results = parse_detections(picam2.capture_metadata())


        if (len(last_results) > 0):
            labels = get_labels()
            for result in last_results:
                label_check = labels[int(result.category)]
                print_checker = f"label_checker is : {label_check}"
                #print(label_check) to print what is being seen
                #this is where you change object being detcted
                if label_check == 'person':
                #do recording of video here
                    time_stamp = record_bird(output2)
                 


