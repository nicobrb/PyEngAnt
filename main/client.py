import numpy as np
import socketio
import base64
import time
import cv2
import datetime
import pandas
import matplotlib.pyplot as plt
from tkinter import *
from PIL import ImageTk, Image
from io import BytesIO
from client_ui import Graphics
import client_ui
from multiprocessing import *


# fps_enum = {1: 1000, 2: 500, 3: 330, 4: 250, 6: 166, 7: 143, 8: 125, 9: 111, 10: 100}
# playback_rate_enum = {1: 1, 2: 0.5, 3: 0.333, 4: 0.25, 5: 0.2, 6: 0.166, 7: 0.142, 8: 0.125, 9: 0.111, 10: 0.1}
DEFAULT_ENG_VALUE = 'null'
DEFAULT_IMAGE_URI = "./static/images/profile_picture.png"  # default image into the video frame section
DEFAULT_FPS_RATE = 10
DEFAULT_PLAYBACK_RATE = 10

ENCODING = "utf-8"

# socket.io params to establish a WebSocket Connection

sio = socketio.Client(
    reconnection=True,
    reconnection_attempts=3,
    reconnection_delay=500,
    reconnection_delay_max=500,
    randomization_factor=0.2,
    request_timeout=12000,
    ssl_verify=False)

namespace = "/session"
ping_timeout_counter = 0

input_check = None
stopped = None

end_eng_label = ""

timestamp_start = time.time()
session_id = None
fps = DEFAULT_FPS_RATE
playback = DEFAULT_PLAYBACK_RATE
starting_seq_size = 300
message = None
frame_counter = 0
framearr = []
eng_data = {}
save_CSV = False
save_Video = False

q = Queue()

master = Tk()
master.geometry('800x600')
master.minsize(800, 600)
master.state('zoomed')
GUI = Graphics(master, q)


@sio.event(namespace='/session')
def connect():
    print("Client connected")
    session_params = {'fps': fps, 'seq_size': starting_seq_size, 'input_type': 'webcam'}
    sio.emit('check_session_id', session_params, namespace='/session')


@sio.event(namespace='/session')
def check_session_id_response(data):
    global session_id
    session_id = data['session_id']
    print("session_id:", session_id)
    q.put(GUI.edit_log_message("INFO: Connected"))
    q.put(client_ui.update_sio_and_sesh(sio, session_id))


@sio.event(namespace='/session')
def log_message(response):
    global message
    message = response
    q.put(GUI.edit_log_message(message))
    print(response)


@sio.event(namespace='/session')
def output_data(data):
    global frame_counter, framearr, eng_data
    frame_counter += 1
    image_data = data['image_data'].split(",")[1].encode(ENCODING)
    out_frame = Image.open(BytesIO(base64.b64decode(image_data))).resize((500, 400), Image.ANTIALIAS)
    out_image = ImageTk.PhotoImage(out_frame)

    q.put(GUI.img_update(out_image))

    framearr.append(out_frame)
    if frame_counter == 1:
        for key in data['eng_data']:
            eng_data[key] = [data['eng_data'][key]]
    else:
        for key in data['eng_data']:
            eng_data[key].append(data['eng_data'][key])

    q.put(GUI.update_aus(data['eng_data']))
    stop, num_frames = GUI.is_stopped_and_saveable()

    if stop and num_frames == frame_counter:
        frame_counter = 0
        finalize_session()
        framearr = []
        eng_data = {}


@sio.event(namespace='/session')
def connect_error(data):
    print("The connection failed!")


def finalize_session():
    global save_Video, save_CSV

    save_Video, save_CSV = GUI.save_bool_values()
    now = datetime.datetime.now()
    today = now.strftime("%Y%m%d-%H%M%S")

    if save_Video and len(framearr) > 0:
        fourcc = cv2.VideoWriter_fourcc(*'mp4v')
        out = cv2.VideoWriter('../recordings/recording'+today+'.mp4', fourcc,10.0, (500,400))
        for i in range(len(framearr)):
            out.write(cv2.cvtColor(np.array(framearr[i]), cv2.COLOR_BGR2RGB))
        out.release()
        print("video done")

    if save_CSV and len(eng_data) > 0:
        csv_dframe = pandas.DataFrame.from_dict(eng_data)
        csv_dframe['timestamp'] = csv_dframe['timestamp'].apply(
            lambda x: datetime.datetime.fromtimestamp(x).isoformat())

        csv_dframe.to_csv('../savedCSVs/'+today+'.csv', index=True)
        print("csv done")


@sio.event(namespace='/session')
def disconnect():
    global ping_timeout_counter
    GUI.edit_log_message("INFO: Client disconnected.")


def try_connect():
    sio.connect('http://localhost:8083', namespaces=['/session'])


def create_gui():
    master.mainloop()


if __name__ == "__main__":
    t1 = Process(target=try_connect(), args=(q,))
    create_gui()

