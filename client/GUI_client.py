import _queue
import time
import base64
import cv2
import datetime
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from tkinter import *
from tkinter import ttk, filedialog, messagebox
import tkinter.font as tkFont
from PIL import ImageTk, Image
from threading import Thread
from socketio import exceptions
import ctypes
import sys


user32 = ctypes.windll.user32
screensize = user32.GetSystemMetrics(0), user32.GetSystemMetrics(1)

ENCODING = "utf-8"
stopped = True
sockio = None
sesh_id = None
cam_video_pop = None
eng_pop = None
t1 = None
connected = False
input_type = None
num_frames_sent = 0
filename = "/"
starting_img = Image.open("../images/profile_picture.png").resize((400, 300), Image.ANTIALIAS)

if screensize[0] == 1536:
    temp_chart = Figure(figsize=(5, 5), dpi=90)
    temp_chart.add_subplot(111).plot(range(1), range(1))

else:
    temp_chart = Figure(figsize=(4, 4), dpi=90)
    temp_chart.add_subplot(111).plot(range(1), range(1))


def start_streaming(tipo_input, video_url):
    """
    funzione per la gestione dello streaming su GUI. In base al tipo di input deciso dall'utente, il programma
    estrae informazioni dalla sorgente del video attraverso la funzione VideoCapture, estrae un frame ogni tot
    (specificato dal metodo waitkey()), lo codifica in formato stringa a 64bit e lo invia al server.
    @param tipo_input: stringa che riporta se lo streaming è da webcam o da file video
    @param video_url: in caso di file video, stringa che riporta il percorso nel sistema
    """
    global ENCODING, sockio, sesh_id, num_frames_sent
    vc = None
    num_frames_sent = 0
    if tipo_input == "webcam":
        vc = cv2.VideoCapture(0, cv2.CAP_DSHOW)
    elif tipo_input == "video":
        vc = cv2.VideoCapture(video_url)
    else:
        print("ERROR: choose the correct format of video file input.")

    if not vc.isOpened() and tipo_input == 'webcam':
        raise IOError("Cannot open webcam")
    elif not vc.isOpened() and tipo_input == 'video':
        raise IOError("Cannot open video, maybe it does not exist")

    while True:
        rval, frame = vc.read()
        frame = cv2.resize(frame, (500, 400))
        timestamp = str(datetime.datetime.fromtimestamp(time.time()))
        rval, buffer = cv2.imencode('.jpg', frame)
        jpg_as_text = base64.b64encode(buffer)
        jpg_as_text = jpg_as_text.decode(ENCODING)
        jpg_as_text = "image/jpeg," + jpg_as_text
        cv2.waitKey(333)
        try:
            if stopped:
                raise IOError()
            sockio.emit('input_image', {'image': jpg_as_text, 'current_time': timestamp,
                                        'session_id': sesh_id}, namespace='/session')
            num_frames_sent += 1
        except IOError:
            print('Analysis stopped')
            vc.release()
            break


def update_sio_and_sesh(sio, ses_id):
    """
    Riceve in input l'oggetto SocketIo inizializzato dallo script client, aggiornando l'id della sessione in modo
    che l'oggetto GUI possa estrarre le informazioni dalle variabili globali senza contattare il processo che gestisce
    il client.
    @param sio: oggetto SocketIo inizializzato nel processo che esegue lo script client
    @param ses_id: id della sessione, diverso per ogni stream che l'utente decide di inizializzare
    """
    global sockio, sesh_id, connected
    sockio = sio
    sesh_id = ses_id
    connected = True


def start_analysis(final_input, video_url='0'):
    """
    La funzione si assicura che non sia già in run una analisi dell'engagement, effettua una richiesta di connessione
    al server e fa partire un thread per la gestione dello streaming e per l'invio dei frame.
    @param final_input: formato di input scelto dall'utente, stringa del tipo "webcam" oppure "video"
    @param video_url: eventuale percorso nel sistema locale dell'utente per il video da analizzare
    """
    global stopped, t1, temp_chart
    stopped = False
    if not connected:
        try:
            sockio.connect('http://localhost:8083', namespaces=['/session'])
        except exceptions.ConnectionError as e:
            print(e)
        except Exception as e:
            print(e)

    t1 = Thread(target=start_streaming, args=(final_input, video_url))
    t1.start()


def define(tipo_input):
    """
    definisce il comportamento della GUI una volta premuto uno dei due bottoni nell'interfaccia per l'inizio dello
    streaming e dell'analisi: apre il file directory per la ricerca del percorso del file nel caso di streaming
    da video e controlla che il formato sia corretto.
    @param tipo_input: formato di input scelto dall'utente, stringa del tipo "webcam" oppure "video"
    """
    global filename, input_type
    cam_video_pop.destroy()
    input_type = tipo_input
    if input_type == 'video':
        filename = filedialog.askopenfilename(initialdir=filename,
                                              title='select a video',
                                              filetypes=(("mp4 files", "*.mp4"), ("all files", "*.*"),))
        if filename.endswith('.mp4'):
            start_analysis(input_type, filename)
        else:
            print("No video returned")
    else:
        start_analysis(input_type)


class Graphics:
    def __init__(self, root, q):
        """
        costruttore dell'interfaccia grafica scritta con Tkinter. inizializza ogni oggetto grafico nell'interfaccia
        e formalizza il bind tra bottoni/caselle e metodi annessi. Inizializza poi l'analisi della coda contenente
        le chiamate ai metodi derivate dal processo client.
        @param root: RootPane utile per inizializzare la finestra in cui proiettare l'interfaccia. Esso deterrà il focus
        dell'input (mouse e tastiera) e verrà eseguito nel thread principale.
        @param q: coda contenente i metodi utili per la comunicazione tra processi. Si ricorda che GUI e client sono
        eseguiti su processi diversi, ergo l'unico modo per poter comunicare con l'oggetto istanza di questa classe
        è chiamare i metodi attraverso questa coda.
        """
        global starting_img
        self.queue = q
        self.root = root
        self.save_video = BooleanVar()
        self.save_CSV = BooleanVar()
        self.eng_vals = []
        self.frames_array = []

        self.root.title('PyEngAnt')
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)

        if screensize[0] == 1536:
            self.root.call('tk', 'scaling', 1.6)
        else:
            self.root.call('tk', 'scaling', 1.2)
        self.titles_style = tkFont.Font(family="Segoe UI", size=22)
        self.results_style = tkFont.Font(family="Segoe UI", size=18)
        self.lab_style = tkFont.Font(family="Segoe UI", size=10)
        self.buttons_style = tkFont.Font(family="Segoe UI", size=15, weight='bold')
        self.ckbtn_style = tkFont.Font(family="Segoe UI", size=14)
        self.legend_style = tkFont.Font(family="Segoe UI", size=16)

        self.root.configure(background='white')
        self.root.columnconfigure(0, weight=1)
        self.title = Label(self.root, text=' (Py)Engagement Analysis Tool', fg='white', bg='black',
                           font=self.titles_style, anchor='w')
        self.log_message = Label(self.root, text='INFO: Client disconnected', fg='white', bg='black',
                                 font=self.titles_style, anchor='e')

        self.AU_01_label = Label(self.root, text="AU 01 - Inner brow raiser", fg='black', bg='white',
                                 font=self.lab_style)
        self.AU_02_label = Label(self.root, text="AU 02 - Outer brow raiser", fg='black', bg='white',
                                 font=self.lab_style)
        self.AU_04_label = Label(self.root, text="AU 04 - Brow lowerer", fg='black', bg='white', font=self.lab_style)
        self.AU_05_label = Label(self.root, text="AU 05 - Upper lid raiser", fg='black', bg='white',
                                 font=self.lab_style)
        self.AU_06_label = Label(self.root, text="AU 06 - Cheek raiser", fg='black', bg='white', font=self.lab_style)
        self.AU_07_label = Label(self.root, text="AU 07 - Lid tightener", fg='black', bg='white', font=self.lab_style)
        self.AU_09_label = Label(self.root, text="AU 09 - Nose wrinkler", fg='black', bg='white', font=self.lab_style)
        self.AU_10_label = Label(self.root, text="AU 10 - Upper lip raiser", fg='black', bg='white',
                                 font=self.lab_style)
        self.AU_12_label = Label(self.root, text="AU 12 - Lip corner puller", fg='black', bg='white',
                                 font=self.lab_style)
        self.AU_14_label = Label(self.root, text="AU 14 - Dimpler", fg='black', bg='white', font=self.lab_style)
        self.AU_15_label = Label(self.root, text="AU 15 - Lip corner depr.", fg='black', bg='white',
                                 font=self.lab_style)
        self.AU_17_label = Label(self.root, text="AU 17 - Chin raiser", fg='black', bg='white', font=self.lab_style)
        self.AU_20_label = Label(self.root, text="AU 20 - Lip stretcher", fg='black', bg='white', font=self.lab_style)
        self.AU_23_label = Label(self.root, text="AU 23 - Lip thightener", fg='black', bg='white', font=self.lab_style)
        self.AU_25_label = Label(self.root, text="AU 25 - Lips part", fg='black', bg='white', font=self.lab_style)
        self.AU_26_label = Label(self.root, text="AU 26 - Jaw drop", fg='black', bg='white', font=self.lab_style)
        self.AU_45_label = Label(self.root, text="AU 45 - Blink", fg='black', bg='white', font=self.lab_style)
        self.AU_28_label = Label(self.root, text="AU 28 - Lip suck", fg='black', bg='white', font=self.lab_style)

        self.btn_frame = Frame(self.root, bg='white')
        self.ckbtn_frame = Frame(self.btn_frame, bg='white')
        self.chart_frame = Frame(self.root, bg='white')
        self.legend_frame = Frame(self.root, bg='white')
        self.img_frame = Frame(self.root, bg='white')

        chart_canvas = FigureCanvasTkAgg(temp_chart, master=self.chart_frame)
        chart_canvas.draw()
        chart_canvas.get_tk_widget().pack(side=TOP, fill=BOTH, expand=1)

        self.eng_chart_label = Label(self.root, text='ENGAGEMENT CHART', font=self.titles_style, fg='black',
                                     bg='white', anchor='center')

        self.start_button = Button(self.btn_frame, text='Start Analysis', fg='white', bg='blue',
                                   font=self.buttons_style, command=self.cam_or_video)
        self.stop_button = Button(self.btn_frame, text='Stop Analysis', fg='white', bg='red',
                                  font=self.buttons_style, command=self.stop_analysis)

        self.save_video_ckbtn = Checkbutton(self.ckbtn_frame, text='Save Video', bg='white', font=self.ckbtn_style,
                                            variable=self.save_video, onvalue=True, offvalue=False)
        self.save_CSV_ckbtn = Checkbutton(self.ckbtn_frame, text='Save CSV', bg='white', font=self.ckbtn_style,
                                          variable=self.save_CSV, onvalue=True, offvalue=False)

        self.eng_legend = Label(self.legend_frame, text='ENGAGEMENT LEGEND', bg='white', font=self.titles_style)
        self.eng_description = Label(self.legend_frame,
                                     text='from 0 to 0.25 = Not Engaged\nfrom 0.25 to 0.5 = Slightly '
                                          'Engaged\nfrom 0.5 to 0.75 = Engaged\n over 0.75 = Highly Engaged',
                                     bg='white', font=self.legend_style, anchor='center')

        self.prog_AU_01 = ttk.Progressbar(self.root, orient=HORIZONTAL, length=120, mode='determinate')
        self.prog_AU_02 = ttk.Progressbar(self.root, orient=HORIZONTAL, length=120, mode='determinate')
        self.prog_AU_04 = ttk.Progressbar(self.root, orient=HORIZONTAL, length=120, mode='determinate')
        self.prog_AU_05 = ttk.Progressbar(self.root, orient=HORIZONTAL, length=120, mode='determinate')
        self.prog_AU_06 = ttk.Progressbar(self.root, orient=HORIZONTAL, length=120, mode='determinate')
        self.prog_AU_07 = ttk.Progressbar(self.root, orient=HORIZONTAL, length=120, mode='determinate')
        self.prog_AU_09 = ttk.Progressbar(self.root, orient=HORIZONTAL, length=120, mode='determinate')
        self.prog_AU_10 = ttk.Progressbar(self.root, orient=HORIZONTAL, length=120, mode='determinate')
        self.prog_AU_12 = ttk.Progressbar(self.root, orient=HORIZONTAL, length=120, mode='determinate')
        self.prog_AU_14 = ttk.Progressbar(self.root, orient=HORIZONTAL, length=120, mode='determinate')
        self.prog_AU_15 = ttk.Progressbar(self.root, orient=HORIZONTAL, length=120, mode='determinate')
        self.prog_AU_17 = ttk.Progressbar(self.root, orient=HORIZONTAL, length=120, mode='determinate')
        self.prog_AU_20 = ttk.Progressbar(self.root, orient=HORIZONTAL, length=120, mode='determinate')
        self.prog_AU_23 = ttk.Progressbar(self.root, orient=HORIZONTAL, length=120, mode='determinate')
        self.prog_AU_25 = ttk.Progressbar(self.root, orient=HORIZONTAL, length=120, mode='determinate')
        self.prog_AU_26 = ttk.Progressbar(self.root, orient=HORIZONTAL, length=120, mode='determinate')
        self.prog_AU_45 = ttk.Progressbar(self.root, orient=HORIZONTAL, length=120, mode='determinate')
        self.prog_AU_28 = ttk.Progressbar(self.root, orient=HORIZONTAL, length=120, mode='determinate')

        self.AUs_bars_dict = {'AU01_r': self.prog_AU_01, 'AU02_r': self.prog_AU_02, 'AU04_r': self.prog_AU_04,
                              'AU05_r': self.prog_AU_05, 'AU06_r': self.prog_AU_06, 'AU07_r': self.prog_AU_07,
                              'AU09_r': self.prog_AU_09, 'AU10_r': self.prog_AU_10, 'AU12_r': self.prog_AU_12,
                              'AU14_r': self.prog_AU_14, 'AU15_r': self.prog_AU_15, 'AU17_r': self.prog_AU_17,
                              'AU20_r': self.prog_AU_20, 'AU23_r': self.prog_AU_23, 'AU25_r': self.prog_AU_25,
                              'AU26_r': self.prog_AU_26, 'AU45_r': self.prog_AU_45, 'AU28_c': self.prog_AU_28}

        self.AUs_labels_dict = {'AU01_r': self.AU_01_label, 'AU02_r': self.AU_02_label, 'AU04_r': self.AU_04_label,
                                'AU05_r': self.AU_05_label, 'AU06_r': self.AU_06_label, 'AU07_r': self.AU_07_label,
                                'AU09_r': self.AU_09_label, 'AU10_r': self.AU_10_label, 'AU12_r': self.AU_12_label,
                                'AU14_r': self.AU_14_label, 'AU15_r': self.AU_15_label, 'AU17_r': self.AU_17_label,
                                'AU20_r': self.AU_20_label, 'AU23_r': self.AU_23_label, 'AU25_r': self.AU_25_label,
                                'AU26_r': self.AU_26_label, 'AU45_r': self.AU_45_label, 'AU28_c': self.AU_28_label}

        self.default_image = ImageTk.PhotoImage(starting_img)
        self.img_canvas = Label(self.img_frame, image=self.default_image, anchor='center')

        self.title.grid(row=0, column=0, columnspan=6, sticky='ew')
        self.img_frame.grid(row=1, column=0, rowspan=9, columnspan=3, padx=10, pady=10)
        self.img_canvas.pack(fill='both')
        self.log_message.grid(row=0, column=5, columnspan=3, sticky='ew')

        self.chart_frame.grid(row=9, column=3, rowspan=8, columnspan=5, sticky='nsew')
        self.eng_chart_label.grid(row=17, column=3, columnspan=8, sticky='nsew')
        self.btn_frame.grid(row=10, column=0, columnspan=3)
        self.start_button.pack(side=LEFT, fill=X)
        self.ckbtn_frame.pack(side=LEFT, fill=X)
        self.stop_button.pack(side=LEFT, fill=X)
        self.save_video_ckbtn.pack(side=BOTTOM)
        self.save_CSV_ckbtn.pack(side=BOTTOM)
        self.legend_frame.grid(row=11, column=0, columnspan=3, rowspan=6)
        self.eng_legend.grid(row=0)
        self.eng_description.grid(row=1, rowspan=5)

        row = 1
        col = 3
        for key in self.AUs_bars_dict:
            if row == 7:
                col += 1
            self.AUs_labels_dict[key].grid(row=row, column=col, pady=5, padx=10)
            self.AUs_bars_dict[key].grid(row=(row + 1), column=col, padx=10)
            if col == 7 and row < 8:
                col = 3
                row += 2
            elif row != 7:
                col += 1

        self.root.after(2000, self.check_queue_poll, self.queue)

    def check_queue_poll(self, queue):
        """
        metodo che permette al thread principale eseguente l'oggetto istanza della classe Graphics di controllare ogni
        20ms la coda delle chiamate. è possibile modificare l'offset nel metodo root.after().
        Il metodo queue.get(0) esegue un POP dalla coda, secondo il criterio FIFO.
        @param queue: coda contenente i metodi utili per la comunicazione tra processi. Si ricorda che GUI e client sono
        eseguiti su processi diversi, ergo l'unico modo per poter comunicare con l'oggetto istanza di questa classe
        è chiamare i metodi attraverso questa coda.
        """
        global screensize
        try:
            queue.get(0)
        except _queue.Empty:
            pass
        finally:
            self.root.after(20, self.check_queue_poll, queue)

    def set_initial_pic(self):
        self.img_canvas.configure(image=self.default_image, anchor='center')
        self.img_canvas.image = self.default_image

    def update_frame_and_chart(self, latest_frame, latest_eng_value, num_frame, sessione):
        """
        il metodo riceve un frame, aggiorna la GUI, lo aggiunge all'array dei frame insieme ai valori di engagement
        (utili per effettuare il rendering del video e il salvataggio nel CSV una volta terminata la sessione), poi
        aggiorna il chart nel caso in cui il valore di engagement sia stato ricevuto/aggiornato (non avverrà prima dei
        300 frame).
        @param latest_frame: frame da mostrare in tempo reale
        @param latest_eng_value: valore di engagement per il grafico e per il valore da comunicare all'utente una volta
        terminata la sessione
        @param num_frame: indice dei frame totali che sono stati ricevuti in questa sessione, utile per sapere ogni
        quanto aggiornare il grafico
        @param sessione: intero per controllare che il frame ricevuto corrisponda alla sessione che è inizializzata
        attualmente.
        """
        global temp_chart, sesh_id
        if not stopped and sessione == sesh_id:
            self.img_canvas.configure(image=latest_frame, anchor='center')
            self.img_canvas.image = latest_frame
            if latest_eng_value is not None:
                self.eng_vals.append(latest_eng_value)
                self.frames_array.append(num_frame)
            if len(self.eng_vals) > 0 and num_frame % 50 == 0:
                if screensize[0] == 1536:
                    temp_chart = Figure(figsize=(5, 5), dpi=90)
                else:
                    temp_chart = Figure(figsize=(4, 4), dpi=90)
                temp_chart.add_subplot(111).plot(self.frames_array, self.eng_vals, "-r")
                for chart in self.chart_frame.winfo_children():
                    chart.destroy()
                chart_canvas = FigureCanvasTkAgg(temp_chart, master=self.chart_frame)
                chart_canvas.draw()
                chart_canvas.get_tk_widget().pack(side=TOP, fill=BOTH, expand=1)

    def edit_log_message(self, message):
        self.log_message.configure(text=message + ' ')

    def reset_aus(self):
        """
        resetta le progress bar nell'interfaccia
        """
        for key in self.AUs_bars_dict:
            self.AUs_bars_dict[key]['value'] = 0

    def update_aus(self, eng_values):
        """
        aggiorna le progress bar con i parametri del volto richiesti, una volta per ogni frame
        @param eng_values: valori reali di engagement, ovvero parametri del volto contenuti nell'intervallo [0,1]
        """
        if not stopped:
            for key in self.AUs_bars_dict:
                try:
                    if key == "AU28_c":
                        valeur = (eng_values[key] * 100)
                        self.AUs_bars_dict[key]['value'] = valeur
                    else:
                        valeur = (eng_values[key] * 100) / 5
                        self.AUs_bars_dict[key]['value'] = valeur
                except TypeError:
                    # print("No face detected for this frame")
                    self.reset_aus()
                    break

    def stop_analysis(self, from_on_close=False):
        """
        esegue una richiesta di disconnessione una volta che l'utente decide di terminare il processo di analisi, sia
        in caso di terminazione naturale (attraverso il bottone "Stop Analysis") oppure di chiusura forzata
        dell'interfaccia. Nel caso della prima, resetta l'interfaccia e inizializza una finestra popup che comunica
        all'utente i risultati finali dell'engagement.
        @param from_on_close: booleano per capire se il processo di analisi va fermata in caso di chiusura della
        finestra
        """
        global stopped, connected, input_type
        if from_on_close:
            stopped = True
            sockio.disconnect()
        elif not stopped:
            stopped = True
            if input_type == 'webcam':
                sockio.emit('client_disconnect_request', namespace='/session')
            elif input_type == 'video':
                sockio.emit('client_video_end_disconnect_request', namespace='/session')
            connected = False
            self.set_initial_pic()
            self.reset_aus()

            if not len(self.eng_vals) > 0:
                self.final_eng("Not much datas for analysis")
            else:
                engagement = self.eng_vals[-1]
                if 0 < engagement <= 0.25:
                    eng_string = 'Not Engaged'
                elif 0.25 < engagement <= 0.5:
                    eng_string = 'Slightly Engaged'
                elif 0.5 < engagement <= 0.75:
                    eng_string = 'Engaged'
                else:
                    eng_string = 'Highly Engaged'

                self.final_eng("Ending engagement value: " + str(round(engagement, 2)) + " -> " + eng_string)

    def cam_or_video(self):
        """
        metodo per inizializzare una finestra di popup per richiedere all'utente la sorgente della riproduzione
        utile all'analisi.
        """
        global cam_video_pop
        cam_video_pop = Toplevel(self.root)
        cam_video_pop.title('INPUT')
        cam_video_pop.config(bg='white')
        cam_video_pop.grab_set()

        pop_label = Label(cam_video_pop, text='Choose a video input', bg='white', font=self.titles_style)
        pop_label.grid(row=0, column=0, columnspan=2, sticky='ew', padx=10, pady=10)

        cam_btn = Button(cam_video_pop, text='Webcam', command=lambda: define('webcam'), font=self.buttons_style)
        video_btn = Button(cam_video_pop, text='Video', command=lambda: define('video'), font=self.buttons_style)
        cam_btn.grid(row=1, column=0, padx=10, pady=20)
        video_btn.grid(row=1, column=1, padx=10, pady=20)

    def final_eng(self, result_text):
        """
        metodo che costruisce il popup per la comunicazione dell'esito dell'engagement.
        @param result_text: stringa di testo con esito dell'engagement.
        """
        global eng_pop
        eng_pop = Toplevel(self.root)
        eng_pop.title('Analysis result')
        eng_pop.config(bg='white')
        eng_pop.grab_set()

        eng_result_pop_label = Label(eng_pop, text='Ending engagement result:', bg='white',
                                     font=self.results_style, anchor='center')
        not_successful_label = Label(eng_pop, text=result_text, bg='white',
                                     font=self.titles_style, anchor='center')
        eng_result_pop_label.pack(pady=20, padx=5)
        not_successful_label.pack(pady=20, padx=5)

    def save_bool_values(self):
        return bool(self.save_video.get()), bool(self.save_CSV.get())

    def is_stopped_and_saveable(self):
        """
        il metodo non è statico perché non c'è modo di risalire ai parametri globali per sapere se la riproduzione
        è in corso o meno, proprio per la natura multiprocess del programma (la scelta di utilizzare Python ha portato
        a questa soluzione).
        @return: coppia di valori, stopped è un booleano riporta se la sessione è in esecuzione o meno, num_frames_sent
        riporta un intero con il numero totale di frames inviati, utile per coordinare il processo client con il
        processo GUI, visto che quest'ultimo è l'addetto all'invio dei frames ma è il primo a riceverli, da qui la
        necessità di allineare entrambi i processi sul numero di frames ricevuti.
        """
        global stopped, num_frames_sent
        return stopped, num_frames_sent

    def on_closing(self):
        """
        gestisce il comportamento del programma alla chiusura del client attraverso terminazione del processo GUI,
        ovvero alla chiusura della finestra.
        """
        if messagebox.askokcancel("Quit", "Do you want to quit?"):
            if not stopped:
                self.stop_analysis(from_on_close=True)
            elif connected:
                sockio.disconnect()
            self.root.destroy()

