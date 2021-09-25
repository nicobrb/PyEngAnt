import _queue
import time
import base64
import tkinter

import cv2
import datetime
from tkinter import *
from tkinter import ttk, filedialog
import tkinter.font as tkFont
from PIL import ImageTk, Image
from threading import Thread

ENCODING = "utf-8"
stopped = True
sockio = None
sesh_id = None
pop = None
t1 = None
num_frames_sent = 0
filename = "/"
starting_img = Image.open("../images/profile_picture.png").resize((500, 400), Image.ANTIALIAS)
SENTINEL = 'STOP'


# TODO: save video before closing frame
# TODO: save video if client disconnects

def start_streaming(input_type, video_url):

    global ENCODING, sockio, sesh_id, num_frames_sent
    vc = None
    num_frames_sent = 0
    if input_type == "webcam":
        vc = cv2.VideoCapture(0, cv2.CAP_DSHOW)
    elif input_type == "video":
        vc = cv2.VideoCapture(video_url)
    else:
        print("ERROR: choose the correct format of video file input.")

    if not vc.isOpened() and input_type == 'webcam':
        raise IOError("Cannot open webcam")
    elif not vc.isOpened() and input_type == 'video':
        raise IOError("Cannot open video, maybe it does not exist")

    while True:
        rval, frame = vc.read()
        frame = cv2.resize(frame, (500, 400))
        timestamp = str(datetime.datetime.fromtimestamp(time.time()))
        rval, buffer = cv2.imencode('.jpg', frame)
        jpg_as_text = base64.b64encode(buffer)
        jpg_as_text = jpg_as_text.decode(ENCODING)
        jpg_as_text = "image/jpeg," + jpg_as_text
        cv2.waitKey(1000)
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
    global sockio, sesh_id
    sockio = sio
    sesh_id = ses_id


def start_analysis(final_input, video_url='0'):
    global stopped, t1
    stopped = False
    t1 = Thread(target=start_streaming, args=(final_input, video_url))
    t1.start()


def define(tipo_input):
    global filename
    pop.destroy()

    if tipo_input == 'video':
        filename = filedialog.askopenfilename(initialdir=filename,
                                              title='select a video',
                                              filetypes=(("mp4 files", "*.mp4"), ("all files", "*.*"),))
        if filename.endswith('.mp4'):
            start_analysis(tipo_input, filename)
        else:
            print("No video returned")
    else:
        start_analysis(tipo_input)


class Graphics:
    def __init__(self, root, q):
        global starting_img
        self.queue = q
        self.root = root
        self.save_video = BooleanVar()
        self.save_CSV = BooleanVar()

        self.root.title('PyEngAnt')
        self.titles_style = tkFont.Font(family="Segoe UI", size=25)
        self.lab_style = tkFont.Font(family="Segoe UI", size=10)
        self.buttons_style = tkFont.Font(family="Segoe UI", size=15, weight='bold')
        self.ckbtn_style = tkFont.Font(family="Segoe UI", size=14)

        root.configure(background='white')
        root.columnconfigure(0, weight=1)
        self.title = Label(root, text=' PyEngAnT', fg='white', bg='black', font=self.titles_style, anchor='w')
        self.log_message = Label(root, text='INFO: Client disconnected', fg='white', bg='black',
                                 font=self.titles_style, anchor='e')
        self.eng_ant_label = Label(root, text=' Engagement Analysis Tool', fg='black', bg='white',
                                   font=self.titles_style, anchor='w')

        self.AU_01_label = Label(root, text="AU 01 - Inner brow raiser", fg='black', bg='white', font=self.lab_style)
        self.AU_02_label = Label(root, text="AU 02 - Outer brow raiser", fg='black', bg='white', font=self.lab_style)
        self.AU_04_label = Label(root, text="AU 04 - Brow lowerer", fg='black', bg='white', font=self.lab_style)
        self.AU_05_label = Label(root, text="AU 05 - Upper lid raiser", fg='black', bg='white', font=self.lab_style)
        self.AU_06_label = Label(root, text="AU 06 - Cheek raiser", fg='black', bg='white', font=self.lab_style)
        self.AU_07_label = Label(root, text="AU 07 - Lid tightener", fg='black', bg='white', font=self.lab_style)
        self.AU_09_label = Label(root, text="AU 09 - Nose wrinkler", fg='black', bg='white', font=self.lab_style)
        self.AU_10_label = Label(root, text="AU 10 - Upper lip raiser", fg='black', bg='white', font=self.lab_style)
        self.AU_12_label = Label(root, text="AU 12 - Lip corner puller", fg='black', bg='white', font=self.lab_style)
        self.AU_14_label = Label(root, text="AU 14 - Dimpler", fg='black', bg='white', font=self.lab_style)
        self.AU_15_label = Label(root, text="AU 15 - Lip corner depressor", fg='black', bg='white', font=self.lab_style)
        self.AU_17_label = Label(root, text="AU 17 - Chin raiser", fg='black', bg='white', font=self.lab_style)
        self.AU_20_label = Label(root, text="AU 20 - Lip stretcher", fg='black', bg='white', font=self.lab_style)
        self.AU_23_label = Label(root, text="AU 23 - Lip thightener", fg='black', bg='white', font=self.lab_style)
        self.AU_25_label = Label(root, text="AU 25 - Lips part", fg='black', bg='white', font=self.lab_style)
        self.AU_26_label = Label(root, text="AU 26 - Jaw drop", fg='black', bg='white', font=self.lab_style)
        self.AU_45_label = Label(root, text="AU 45 - Blink", fg='black', bg='white', font=self.lab_style)
        self.AU_28_label = Label(root, text="AU 28 - Lip suck", fg='black', bg='white', font=self.lab_style)

        self.start_button = Button(root, text='Start Analysis', fg='white', bg='blue', font=self.buttons_style,
                                   command=self.cam_or_video)
        self.stop_button = Button(root, text='Stop Analysis', fg='white', bg='red', font=self.buttons_style,
                                  command=self.stop_analysis)
        self.save_video_ckbtn = Checkbutton(root, text='Save Video', bg='white', font=self.ckbtn_style,
                                            variable=self.save_video, onvalue=True, offvalue=False)
        self.save_CSV_ckbtn = Checkbutton(root, text='Save CSV', bg='white', font=self.ckbtn_style,
                                          variable=self.save_CSV, onvalue=True, offvalue=False)

        self.prog_AU_01 = ttk.Progressbar(root, orient=HORIZONTAL, length=150, mode='determinate')
        self.prog_AU_02 = ttk.Progressbar(root, orient=HORIZONTAL, length=150, mode='determinate')
        self.prog_AU_04 = ttk.Progressbar(root, orient=HORIZONTAL, length=150, mode='determinate')
        self.prog_AU_05 = ttk.Progressbar(root, orient=HORIZONTAL, length=150, mode='determinate')
        self.prog_AU_06 = ttk.Progressbar(root, orient=HORIZONTAL, length=150, mode='determinate')
        self.prog_AU_07 = ttk.Progressbar(root, orient=HORIZONTAL, length=150, mode='determinate')
        self.prog_AU_09 = ttk.Progressbar(root, orient=HORIZONTAL, length=150, mode='determinate')
        self.prog_AU_10 = ttk.Progressbar(root, orient=HORIZONTAL, length=150, mode='determinate')
        self.prog_AU_12 = ttk.Progressbar(root, orient=HORIZONTAL, length=150, mode='determinate')
        self.prog_AU_14 = ttk.Progressbar(root, orient=HORIZONTAL, length=150, mode='determinate')
        self.prog_AU_15 = ttk.Progressbar(root, orient=HORIZONTAL, length=150, mode='determinate')
        self.prog_AU_17 = ttk.Progressbar(root, orient=HORIZONTAL, length=150, mode='determinate')
        self.prog_AU_20 = ttk.Progressbar(root, orient=HORIZONTAL, length=150, mode='determinate')
        self.prog_AU_23 = ttk.Progressbar(root, orient=HORIZONTAL, length=150, mode='determinate')
        self.prog_AU_25 = ttk.Progressbar(root, orient=HORIZONTAL, length=150, mode='determinate')
        self.prog_AU_26 = ttk.Progressbar(root, orient=HORIZONTAL, length=150, mode='determinate')
        self.prog_AU_45 = ttk.Progressbar(root, orient=HORIZONTAL, length=150, mode='determinate')
        self.prog_AU_28 = ttk.Progressbar(root, orient=HORIZONTAL, length=150, mode='determinate')

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
        self.img_canvas = Label(image=self.default_image, anchor='w')

        self.title.grid(row=0, column=0, columnspan=6, sticky='ew')
        self.eng_ant_label.grid(row=1, column=0, columnspan=2, sticky='ew')
        self.img_canvas.grid(row=2, column=0, rowspan=6, columnspan=2, padx=10, sticky='nsew')
        self.log_message.grid(row=0, column=6, columnspan=3, sticky='ew')

        self.start_button.grid(row=9, column=0, pady=10, padx=10, sticky='w')
        self.stop_button.grid(row=9, column=1, padx=10, sticky='w')
        self.save_video_ckbtn.grid(row=10, column=0, padx=10, sticky='w')
        self.save_CSV_ckbtn.grid(row=11, column=0, padx=10, sticky='w')

        row = 1
        col = 2
        for key in self.AUs_bars_dict:
            self.AUs_labels_dict[key].grid(row=row, column=col, padx=10)
            self.AUs_bars_dict[key].grid(row=(row + 1), column=col, padx=10)
            if col == 7 and row < 8:
                col = 2
                row += 2
            else:
                col += 1

        self.root.after(1000, self.check_queue_poll, self.queue)

    def check_queue_poll(self, queue):
        try:
            queue.get(0)
        except _queue.Empty:
            pass
        finally:
            self.root.after(20, self.check_queue_poll, queue)

    def set_initial_pic(self):
        self.img_canvas.configure(image=self.default_image)
        self.img_canvas.image = self.default_image

    def img_update(self, new_frame):
        if not stopped:
            self.img_canvas.configure(image=new_frame)
            self.img_canvas.image = new_frame
        else:
            return

    def edit_log_message(self, message):
        self.log_message.configure(text=message + ' ')

    def reset_aus(self):
        for key in self.AUs_bars_dict:
            self.AUs_bars_dict[key]['value'] = 0

    def update_aus(self, eng_values):
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

    def stop_analysis(self):
        global stopped
        stopped = True
        self.set_initial_pic()
        self.reset_aus()
        self.queue.put(SENTINEL)

    def cam_or_video(self):

        global pop
        pop = Toplevel(self.root)
        pop.title('INPUT')
        pop.geometry("350x150")
        pop.config(bg='white')
        pop.grab_set()

        pop_label = Label(pop, text='Choose a video input', bg='white', font=self.titles_style)
        pop_label.grid(row=0, column=0, columnspan=2, sticky='ew', padx=10, pady=10)

        cam_btn = Button(pop, text='Webcam', command=lambda: define('webcam'), font=self.buttons_style)
        video_btn = Button(pop, text='Video', command=lambda: define('video'), font=self.buttons_style)
        cam_btn.grid(row=1, column=0, padx=10, pady=20)
        video_btn.grid(row=1, column=1, padx=10, pady=20)

    def save_bool_values(self):
        return bool(self.save_video.get()), bool(self.save_CSV.get())

    def is_stopped_and_saveable(self):
        global stopped, num_frames_sent
        return stopped, num_frames_sent
