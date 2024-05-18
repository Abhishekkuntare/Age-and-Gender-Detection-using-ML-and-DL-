import cv2
import numpy as np
import math
import argparse
from flask import Flask, render_template, Response, request
from PIL import Image
import io

# step 1: import all packages
# cv2: OpenCV library for computer vision tasks.
# numpy: NumPy for numerical operations.
# math: Standard math library.
# argparse: Handles command-line arguments.
# Flask: Web application framework for creating the user interface.
# PIL: Python Imaging Library for image processing.
# io: Input/Output operations.

# step 2: Configures Flask with an upload folder where uploaded files will be stored.
UPLOAD_FOLDER = './UPLOAD_FOLDER'
app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER



# step 3: Face detection function Defines a function (highlightFace) for face detection.
# Uses a pre-trained deep learning face detection model (net) to identify faces in the given frame.
# Draws rectangles around the detected faces based on confidence levels.
def highlightFace(net, frame, conf_threshold=0.7):
    frameOpencvDnn = frame.copy()
    frameHeight = frameOpencvDnn.shape[0]
    frameWidth = frameOpencvDnn.shape[1]
    # Grab the frame dimensions and convert it to a blob.
    blob = cv2.dnn.blobFromImage(frameOpencvDnn, 1.0, (300, 300), [
                                 104, 117, 123], True, False)
    # Pass the blob through the network and obtain the detections and predictions.
    net.setInput(blob)
    # net.forward() method detects the faces and stores the data in detections
    detections = net.forward()

    faceBoxes = []

    # This for loop is for drawing rectangle on detected face.
    for i in range(detections.shape[2]):    # Looping over the detections.
        # Extract the confidence (i.e., probability) associated with the prediction.
        confidence = detections[0, 0, i, 2]
        if confidence > conf_threshold:   # Compare it to the confidence threshold.
            # Compute the (x, y)-coordinates of the bounding box for the face.
            x1 = int(detections[0, 0, i, 3]*frameWidth)
            y1 = int(detections[0, 0, i, 4]*frameHeight)
            x2 = int(detections[0, 0, i, 5]*frameWidth)
            y2 = int(detections[0, 0, i, 6]*frameHeight)
            # Drawing the bounding box of the face.
            faceBoxes.append([x1, y1, x2, y2])
            cv2.rectangle(frameOpencvDnn, (x1, y1), (x2, y2),
                          (0, 255, 0), int(round(frameHeight/150)), 8)
    return frameOpencvDnn, faceBoxes



# step 4:Uses argparse to parse command-line arguments.
# Expects an optional --image argument for providing the input image file.
# Gives input img to the prg for detection.
# Using argparse library which was imported.
parser = argparse.ArgumentParser()
# If the input argument is not given it will skip this and open webcam for detection
parser.add_argument('--image')

args = parser.parse_args()



# step 5: Frame Generation Function:
# Defines a function (gen_frames) for generating video frames from a webcam feed.
# Initializes pre-trained models for face detection, age prediction, and gender prediction.
# Captures video from the default camera and processes each frame.
# Detects faces, predicts age and gender, and sends processed frames to the web page for streaming.


def gen_frames():
    faceProto = "opencv_face_detector.pbtxt"#Prototxt files describe the architecture of neural network models in a human-readable format. 
    faceModel = "opencv_face_detector_uint8.pb"#file contains the trained weights and parameters of the face detection model. It's a serialized representation of the model that can be loaded and used for inference.
    ageProto = "age_deploy.prototxt"
    ageModel = "age_net.caffemodel"
    genderProto = "gender_deploy.prototxt"
    genderModel = "gender_net.caffemodel" #file contains the trained weights and parameters of the age prediction model.

    MODEL_MEAN_VALUES = (78.4263377603, 87.7689143744, 114.895847746)
    # Defining age range.
    ageList = ['(0-2)', '(4-6)', '(8-12)', '(15-21)',
               '(21-25)','(26-32)', '(38-43)', '(44-50)','(51-61)' '(62-100)']
    genderList = ['Male', 'Female']
 
    # LOAD NETWORK
    faceNet = cv2.dnn.readNet(faceModel, faceProto)
    ageNet = cv2.dnn.readNet(ageModel, ageProto)
    genderNet = cv2.dnn.readNet(genderModel, genderProto)

# Open a video file or an image file or a camera stream
    video = cv2.VideoCapture(0)
    padding = 20
    while cv2.waitKey(1) < 0:
        # Read frame
        hasFrame, frame = video.read()
        if not hasFrame:
            cv2.waitKey()
            break

    # It will detect the no. of faces in the frame
        resultImg, faceBoxes = highlightFace(faceNet, frame)
        if not faceBoxes:   # If no faces are detected
            print("No face detected")   # Then it will print this message

        for faceBox in faceBoxes:
            # print facebox
            face = frame[max(0, faceBox[1]-padding):   # Face info is stored in this variable
                         min(faceBox[3]+padding, frame.shape[0]-1), max(0, faceBox[0]-padding):min(faceBox[2]+padding, frame.shape[1]-1)]

        # The dnn.blobFromImage takes care of pre-processing
        # which includes setting the blob  dimensions and normalization.
            blob = cv2.dnn.blobFromImage(
                face, 1.0, (227, 227), MODEL_MEAN_VALUES, swapRB=False)
            genderNet.setInput(blob)
        # genderNet.forward method will detect the gender of each face detected
            genderPreds = genderNet.forward()
            gender = genderList[genderPreds[0].argmax()]
            print(f'Gender: {gender}')  # print the gender in the console

            ageNet.setInput(blob)
        # ageNet.forward method will detect the age of the face detected
            agePreds = ageNet.forward()
            age = ageList[agePreds[0].argmax()]
            print(f'Age: {age[1:-1]} years')    # print the age in the console

        # Show the output frame
            cv2.putText(resultImg, f'{gender}, {age}', (
                faceBox[0], faceBox[1]-10), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 255), 2, cv2.LINE_AA)
        #cv2.imshow("Detecting age and gender", resultImg)

            if resultImg is None:
                continue

            ret, encodedImg = cv2.imencode('.jpg', resultImg)
            #resultImg = buffer.tobytes()
            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + bytearray(encodedImg) + b'\r\n')



# manually select img from the system 
def gen_frames_photo(img_file): 
    faceProto = "opencv_face_detector.pbtxt"
    faceModel = "opencv_face_detector_uint8.pb"
    ageProto = "age_deploy.prototxt"# it describes the architecture of the age prediction model.
    ageModel = "age_net.caffemodel"
    genderProto = "gender_deploy.prototxt"
    genderModel = "gender_net.caffemodel"

    MODEL_MEAN_VALUES = (78.4263377603, 87.7689143744, 114.895847746)
    # Defining age range.
    ageList = ['(0-2)', '(4-6)', '(8-12)', '(15-20)',
               '(21-32)', '(38-43)', '(44-60)', '(61-80)', '(81-100)']
    genderList = ['Male', 'Female']

    # LOAD NETWORK
    faceNet = cv2.dnn.readNet(faceModel, faceProto)
    ageNet = cv2.dnn.readNet(ageModel, ageProto)
    genderNet = cv2.dnn.readNet(genderModel, genderProto)

# Open a video file or an image file or a camera stream

    frame = cv2.cvtColor(img_file, cv2.COLOR_BGR2RGB)
    #frame = img_file
    #hasFrame, frame = img_file.read()
    #ret, frame = cv2.imencode('.jpg', img_file)
    #video = cv2.VideoCapture(img_file)
    padding = 20
    while cv2.waitKey(1) < 0:
        # Read frame
        #hasFrame, frame = video.read()
        # if not hasFrame:
        # cv2.waitKey()
        # break

        # It will detect the no. of faces in the frame
        resultImg, faceBoxes = highlightFace(faceNet, frame)
        if not faceBoxes:   # If no faces are detected
            print("No face detected")   # Then it will print this message

        for faceBox in faceBoxes:
            # print facebox
            face = frame[max(0, faceBox[1]-padding):   # Face info is stored in this variable
                         min(faceBox[3]+padding, frame.shape[0]-1), max(0, faceBox[0]-padding):min(faceBox[2]+padding, frame.shape[1]-1)]

        # The dnn.blobFromImage takes care of pre-processing
        # which includes setting the blob  dimensions and normalization.
            blob = cv2.dnn.blobFromImage(
                face, 1.0, (227, 227), MODEL_MEAN_VALUES, swapRB=False)
            genderNet.setInput(blob)
        # genderNet.forward method will detect the gender of each face detected
            genderPreds = genderNet.forward()
            gender = genderList[genderPreds[0].argmax()]
            print(f'Gender: {gender}')  # print the gender in the console

            ageNet.setInput(blob)
        # ageNet.forward method will detect the age of the face detected
            agePreds = ageNet.forward()
            age = ageList[agePreds[0].argmax()]
            print(f'Age: {age[1:-1]} years')    # print the age in the console

        # Show the output frame
            cv2.putText(resultImg, f'{gender}, {age}', (
                faceBox[0], faceBox[1]-10), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 255), 2, cv2.LINE_AA)
        #cv2.imshow("Detecting age and gender", resultImg)

            if resultImg is None:
                continue

            ret, encodedImg = cv2.imencode('.jpg', resultImg)
            #resultImg = buffer.tobytes()
            return (b'--frame\r\n'
                    b'Content-Type: image/jpeg\r\n\r\n' + bytearray(encodedImg) + b'\r\n')



# step 6: web application routes Defines Flask routes for different functionalities.
# /: Renders the home page.
@app.route('/')
def index():
    """Video streaming home page."""
    return render_template('index.html')

@app.route('/video_feed')
def video_feed():
    # Video streaming route. Put this in the src attribute of an img tag
    return Response(gen_frames(), mimetype='multipart/x-mixed-replace; boundary=frame')

@app.route('/webcam')
def webcam():
    return render_template('webcam.html')

@app.route('/upload', methods=['GET', 'POST'])

def upload_file():
    if request.method == 'POST':
        f = request.files['fileToUpload'].read()
        img = Image.open(io.BytesIO(f))
        img_ip = np.asarray(img, dtype="uint8")
        print(img_ip)
        return Response(gen_frames_photo(img_ip), mimetype='multipart/x-mixed-replace; boundary=frame')
        # return 'file uploaded successfully'

if __name__ == '__main__':
    app.run(debug=True)
