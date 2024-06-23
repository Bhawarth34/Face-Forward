from flask import Flask, render_template, Response, request
from flask_socketio import SocketIO, emit
import cv2
import os
import AWSConnect
from werkzeug.utils import secure_filename

UPLOAD_FOLDER = "./uploaded_image"
ALLOWED_EXTENSIONS = {'jpg', 'jpeg', 'png'}

app = Flask(__name__)
socket = SocketIO(app)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

classifier = cv2.CascadeClassifier(cv2.data.haarcascades + "haarcascade_frontalface_default.xml")

camera = cv2.VideoCapture(0)  

def detect_bounding_box(vid):
    gray_image = cv2.cvtColor(vid, cv2.COLOR_BGR2GRAY)
    faces = classifier.detectMultiScale(gray_image, 1.1, 5, minSize=(40, 40))
    for (x, y, w, h) in faces:
        cv2.rectangle(vid, (x, y), (x + w, y + h), (0, 255, 0), 4)
        if(not os.path.exists("face.png")):
            cv2.imwrite("face.png", vid)
            data = AWSConnect.find_face("face.png")
            socket.emit("Facedata", data)
    return faces

def gen_frames():  # generate frame by frame from camera
    while True:

        success, frame = camera.read()  # read the camera frame
        if not success:
            break
        else:
            faces = detect_bounding_box(frame)
            ret, buffer = cv2.imencode('.jpg', frame)
            frame = buffer.tobytes()
            yield (b'--frame\r\n'
                    b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')  # concat frame one by one and show result


@app.route('/video_feed')
def video_feed():
    #Video streaming route. Put this in the src attribute of an img tag
    return Response(gen_frames(), mimetype='multipart/x-mixed-replace; boundary=frame')


@app.route('/')
def index():
    """Video streaming home page."""
    return render_template('index.html')

@app.route('/add/student')
def showAddStudent():
    return render_template('addStudent.html')

@app.post('/add/student')
def addStudent():
    name = request.form.get("name")
    uid = request.form.get("uid")
    course = request.form.get("course")
    section = request.form.get("section")
    file = request.files['imageFile']

    if file:
        filename = secure_filename(file.filename)
        file.save(os.path.join(app.config["UPLOAD_FOLDER"], filename))

        res = AWSConnect.add_student_data(name, uid, course, section, filename, "student-facedata")
        if(res):
            return render_template('index.html', uploaded="true")
        else:
            return render_template('index.html', uploaded="false")
    return render_template('addStudent.html')

if __name__ == '__main__':
    app.run(debug=True)
