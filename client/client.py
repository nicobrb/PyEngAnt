import GUI_client
import socketio
import base64
import time
import cv2
import datetime
import pandas
import numpy as np
from tkinter import *
from PIL import ImageTk, Image
from io import BytesIO
from GUI_client import Graphics
from socketio import exceptions
from multiprocessing import *


DEFAULT_ENG_VALUE = 'null'
DEFAULT_IMAGE_URI = "./static/images/profile_picture.png"  # default image into the video frame section
DEFAULT_FPS_RATE = 10

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
starting_seq_size = 300
message = None
frame_counter = 0
framearr = []
eng_data = {}
save_CSV = False
save_Video = False

q = Queue()

master = Tk()
master.minsize(800, 600)
master.state('zoomed')
GUI = Graphics(master, q)


@sio.event(namespace=namespace)
def connect():
    session_params = {'fps': fps, 'seq_size': starting_seq_size, 'input_type': 'webcam'}
    sio.emit('check_session_id', session_params, namespace=namespace)
    print("Client connected")


@sio.event(namespace=namespace)
def check_session_id_response(data):
    global session_id
    session_id = data['session_id']
    print("session_id:", session_id)
    q.put(GUI.edit_log_message("INFO: Connected"))
    q.put(GUI_client.update_sio_and_sesh(sio, session_id))


@sio.event(namespace=namespace)
def log_message(response):
    global message
    message = response
    q.put(GUI.edit_log_message(message))
    print(response)


@sio.event(namespace=namespace)
def output_data(data):
    """
    la procedura controlla inizialmente che la sessione del frame sia corrispondente a quella attiva (potrebbero esserci
    frame in arrivo derivanti da altre sessioni ma accodate al buffer del server, non ancora elaborati). In seguito
    riconverte il frame da stringa a 64-bit in immagine, attraverso la funzione encode, per poi modificare la GUI.
    in seguito elabora i parametri del volto del suddetto frame e li utilizza per aggiornare le progress bar della GUI.
    @param data: array di informazioni passato dal server, contenente i dati dell'engagement del frame ricevuto
    e il frame modificato dalla componente EngRecApi
    """
    global frame_counter, framearr, eng_data, session_id
    if data['open_id'] == session_id:
        try:
            image_data = data['image_data'].split(",")[1].encode(ENCODING)
            out_frame = Image.open(BytesIO(base64.b64decode(image_data))).resize((400, 300), Image.ANTIALIAS)
            out_image = ImageTk.PhotoImage(out_frame)
            frame_counter += 1
            q.put(GUI.update_frame_and_chart(out_image, data['eng_data']['eng_val'], frame_counter, session_id))
            framearr.append(out_frame)

            if frame_counter == 1:
                for key in data['eng_data']:
                    eng_data[key] = [data['eng_data'][key]]
            else:
                for key in data['eng_data']:
                    eng_data[key].append(data['eng_data'][key])

            q.put(GUI.update_aus(data['eng_data']))

        except RuntimeError:
            print("GUI has been closed!")
    else:
        print("frame from another session received. Discarding...")


@sio.event(namespace=namespace)
def connect_error():
    print("The connection failed!")
    q.put(GUI.edit_log_message("The connection failed!"))


@sio.event(namespace=namespace)
def disconnect():
    """
    Evento che segue la disconnessione del client, svuota l'array dei frame e dei dati.
    """
    global ping_timeout_counter, frame_counter, framearr, eng_data, session_id
    print("Disconnected!")
    finalize_session()
    frame_counter = 0
    framearr = []
    eng_data = {}
    session_id = 0
    q.put(GUI.edit_log_message("INFO: Client disconnected."))


def try_connect():
    """
    Esegue la il tentativo di connessione attraverso l'oggetto Socketio, al client inizializzato in locale.
    Va modificato in caso di cambio dell'url o di server in remoto. Il namespace è predefinito.
    """
    try:
        sio.connect('http://localhost:8083', namespaces=[namespace])
    except exceptions.ConnectionError as e:
        print(e)


def finalize_session():
    """
    Metodo eseguito poco prima della disconnessione del Client o della termine dell'analisi, esso rileva le spunte
    della GUI circa l'intenzione di salvare il file CSV dei dati di engagement e il video dell'analisi. Salva il
    tutto all'interno della cartella del progetto, nel percorso segnalato.
    """
    global save_Video, save_CSV
    save_Video, save_CSV = GUI.save_bool_values()
    now = datetime.datetime.now()
    today = now.strftime("%Y%m%d-%H%M%S")

    if save_Video and len(framearr) > 0:
        fourcc = cv2.VideoWriter_fourcc(*'mp4v')
        out = cv2.VideoWriter('./images/recordings/recording' + today + '.mp4', fourcc, 10.0, (500, 400))
        for i in range(len(framearr)):
            out.write(cv2.cvtColor(np.array(framearr[i]), cv2.COLOR_BGR2RGB))
        out.release()
        print("video done")

    if save_CSV and len(eng_data) > 0:
        csv_dframe = pandas.DataFrame.from_dict(eng_data)
        csv_dframe['timestamp'] = csv_dframe['timestamp'].apply(
            lambda x: datetime.datetime.fromtimestamp(x).isoformat())

        csv_dframe.to_csv('./images/savedCSVs/' + today + '.csv', index=True)
        print("csv done")


if __name__ == "__main__":
    t1 = Process(target=try_connect(), args=(q,))
    master.mainloop()
