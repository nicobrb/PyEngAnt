import requests as r
import threading
from time import sleep, time
import json
import cv2
import sys
import numpy as np
import definitions
import OF_const
import math
import base64
from webptools import grant_permission
from webptools import base64str2webp_base64str

grant_permission()


class EngSession(object):
    STARTING_SEQ_SIZE = 300

    def __init__(self, openface_id, fps):

        self.openface_id = openface_id
        self.face_data_list = []
        self.fps = fps
        self.sequence_size = EngSession.STARTING_SEQ_SIZE
        self.frame_to_process = []
        self.data_to_output = []
        self.frame_counter = 0
        self.last_eng = None
        self.last_output = []
        self.session_valid = True
        self.message = 'Session is valid.'
        self.seq_checker = True

        thread_input = threading.Thread(target=self.keep_analysing, args=())
        thread_input.daemon = True
        thread_input.start()

    def analyze_frame(self, frame=None):
        if not self.frame_to_process:
            return

        # input is an ascii string.
        # image_data = frame
        image_data = self.frame_to_process.pop(0)

        json_to_send = json.dumps({"session_id": self.openface_id, "image": image_data,
                                   "ret_image": True,
                                   "ret_gaze": True,
                                   "ret_head_pose": True,
                                   "ret_aus": True,
                                   })
        self.frame_counter += 1
        timestamp = time()
        eng_data = None
        try:
            response = r.post(url=definitions.OPENFACEAPI_HOST + definitions.OPENFACEAPI_SESSION_ENDPOINT,
                              data=json_to_send,
                              params=[definitions.OPENFACEAPI_SESSION_SECURE_CODE_JSON_PARAM],
                              verify=False)

            if response.status_code >= 200 and response.status_code < 500:
                if response.status_code == 200:
                    print(
                        f"Session {self.openface_id} - Result from OpenFaceApi in {response.elapsed} seconds. Resp "
                        f"size: {sys.getsizeof(response.content)} B")
                    json_obj = response.json()
                    face_data = json_obj.get("face_data")
                    if face_data.get("image") is not None:

                        # capture requested data from openface output
                        image_data = face_data.pop("image")
                        confidence = face_data.pop("confidence")
                        gaze = face_data.pop("gaze")
                        head_pose = face_data.pop("head_pose")
                        au_intensity = face_data.pop("au_intensity")
                        au_presence = face_data.pop("au_presence")

                        # format openface output into a single array for the sequence request
                        eng_data = EngSession.format_openface_datas(self.frame_counter,
                                                                    confidence,
                                                                    timestamp,
                                                                    gaze,
                                                                    head_pose,
                                                                    au_intensity,
                                                                    au_presence)
                        eng_data = [str(x) for x in eng_data]  # convert all values to strings
                        self.addEngData(eng_data)  # add eng data to the sequence array to send

                        if len(self.face_data_list) >= self.sequence_size:

                            # secure params (for threading problems)
                            if self.seq_checker:
                                self.seq_checker = False
                                # adding SEQ_SIZE frames to sequence size for the next sequence to send,
                                # up to evaluate all video
                                self.sequence_size += EngSession.STARTING_SEQ_SIZE
                                sleep(0.01)
                                self.seq_checker = True

                            # create a list that represents a table with an header and sequence content
                            eng_datas_to_send = [OF_const.HEADER_ARR]
                            eng_datas_to_send.extend(self.face_data_list)  # sequence content
                            json_obj = {"face_sequence": eng_datas_to_send}

                            eng_resp = r.post(
                                url=definitions.ENGRECAPI_HOST + definitions.ENGRECAPI_ENGAGEMENT_ENDPOINT,
                                json=json_obj)

                            if eng_resp.status_code == 200:
                                r_json_obj = eng_resp.json()
                                print(
                                    f"Session {self.openface_id} - Result from EngRecApi: {eng_resp.content} in "
                                    f"{eng_resp.elapsed} seconds. Resp size: {sys.getsizeof(eng_resp.content)} B")
                                self.last_eng = r_json_obj.get("eng_level")

                                # emit('last_eng_out',{"eng_level":self.last_eng,"seq_size":self.sequence_size},
                                # namespace='/session')
                            elif eng_resp.status_code == 400:
                                json_obj = response.json()
                                status = json_obj.get("status")
                                message = json_obj.get("message")
                                print(
                                    f"Session {self.openface_id} --- ERROR --- status code:{eng_resp.status_code} - "
                                    f"Message: {message}")
                            elif eng_resp.status_code > 400:
                                self.session_valid = False
                                self.message = f"Session {self.openface_id} --- ERROR --- status code:" \
                                               f"{eng_resp.status_code} - Message: Error with EngRecApi request "

                            # dopo aver ricevuto i dati rimuovo sequence_gap_size record dalla sequenza
                            # self.face_data_list = self.face_data_list[self.sequence_gap_size:self.sequence_size-1]
                elif response.status_code == 204:
                    # Face not found in frame
                    print(
                        f"Session {self.openface_id} --- INFO --- status code:{response.status_code} - Message: Face "
                        f"Not Found")
                elif response.status_code == 206 or response.status_code == 400:
                    # Error: Unauthorized or different Bad Request error 
                    json_obj = response.json()
                    status = json_obj.get("status")
                    message = json_obj.get("message")
                    print(
                        f"Session {self.openface_id} --- ERROR --- status code:{response.status_code} - Message: {message}")
                elif response.status_code > 400:
                    # Any other different error that not involves the server directly
                    json_obj = response.json()
                    status = json_obj.get("status")
                    message = json_obj.get("message")
                    print(
                        f"Session {self.openface_id} --- ERROR --- status code:{response.status_code} - Message: {message}")
                    self.session_valid = False
                    self.message = message
                    return response.status_code, None, None
            else:
                print(
                    f"Session {self.openface_id} --- ERROR --- status code:{response.status_code} - Message: {response.content}")
                raise RuntimeError("ERROR: Server failure.")
        except r.ConnectionError as e:
            # if one of the components is off or not responding
            self.session_valid = False
            self.message = 'Webservers are not responding, abort connection. Check OpenFaceApi or EngRecApi are still ' \
                           'running. '
            print(
                "ERROR: Webservers are not responding, abort connection. Check OpenFaceApi or EngRecApi are still "
                "running.\n",
                e.strerror)
            return 500, None, None
        except r.RequestException as e:
            # if one of the components is off or not responding
            self.session_valid = False
            self.message = 'Webservers are not responding, abort connection. Check OpenFaceApi or EngRecApi are still ' \
                           'running. '
            print(
                "ERROR: Webservers are not responding, abort connection. Check OpenFaceApi or EngRecApi are still "
                "running.\n",
                e.strerror)
            return 500, None, None
        except RuntimeError as e:
            # unexpected situation
            print("ERROR: ", e)
            self.session_valid = False
            self.message = response.content
            return 500, None, None
        except Exception as e:
            # session["openface_id"] = None
            print("ERROR: Unexpected exception.")
            raise

        image_data = image_data.encode("utf-8")
        buffer = base64.b64decode(image_data)
        cv2_img = cv2.imdecode(np.frombuffer(buffer, dtype=np.uint8), flags=cv2.IMREAD_COLOR)

        eng_lev = self.last_eng if self.last_eng is None else round(self.last_eng, 3)

        cv2_img = cv2.putText(cv2_img,
                              str.format("frame:{} - last_eng:{} - frame_analized:{}",
                                         self.frame_counter,
                                         eng_lev,
                                         self.sequence_size - EngSession.STARTING_SEQ_SIZE),
                              (5, 20),
                              cv2.FONT_HERSHEY_PLAIN, 1, (0, 0, 255),  # red color in BGR
                              thickness=1, lineType=1)
        retval, buffer = cv2.imencode('.jpg', cv2_img)  # [int(cv2.IMWRITE_JPEG_QUALITY), 50] for reduce quality image
        b = base64.b64encode(buffer)
        b = b.decode("utf-8")
        image_data = b

        # prepare data retrieved to output
        eng_out = EngSession.format_eng_out(self.frame_counter, timestamp, eng_data, self.last_eng)
        image_data, _ = base64str2webp_base64str(base64str=image_data, image_type="jpg", option="-q 80",
                                                 temp_path="./temp")  # convert from base64 jpg to webp to use whammy.js
        image_data_ret = "data:image/webp;base64," + image_data
        self.data_to_output.append({'image_data': image_data_ret, 'eng_data': eng_out, 'open_id': self.openface_id})
        # emit('output_data', {'image_data': image_data_ret,'eng_data':eng_out}, namespace='/session')
        return 200, image_data_ret, eng_out

    def keep_analysing(self):
        # for threading
        # function that continuosly try to analyze new frames
        while True:
            self.analyze_frame()
            sleep(0.05)

    def get_output_data(self):
        # function that waits an output to be retrieved
        while not self.data_to_output:  # oppure if
            sleep(0.01)
            # return
        data = self.data_to_output.pop(0)
        return data

    def flush_data(self):
        # to delete remaining frames (for threading problems)
        self.frame_to_process = []
        self.data_to_output = []
        self.face_data_list = []
        return True

    def get_session_id(self):
        return self.openface_id

    def is_valid(self):
        # return True or False if the session remains valid
        return self.session_valid

    def get_message(self):
        return self.message

    # for future features
    def set_fps(self, fps):
        self.fps = fps

    def get_fps(self):
        return self.fps

    def addFrame(self, frame):
        # implemented with threading this function adds a frame that has to be analized
        self.frame_to_process.append(frame)

    def addEngData(self, data):
        self.face_data_list.append(data)

    def get_sequence(self, num_frame):
        return

    def format_openface_datas(self, frame, confidence, timestamp, gaze, head_pose, au_i, au_p):
        """
            converts openface outputs in an array that contains all datas

        """
        data = [frame, confidence, timestamp]

        # getting all gaze values (gaze_0_(x/y/z), gaze_1_(x/y/z), gaze_angle_(x/y))
        for gaze_data in gaze.get('gaze_0'):
            data.append(gaze_data)
        for gaze_data in gaze.get('gaze_1'):
            data.append(gaze_data)
        # for gaze_data in gaze.get('gaze_angle'):
        #    data.append(gaze_data)

        # getting all head pose values (pose_T(x/y/z), pose_R(x/y/z))
        for head_pose_data in head_pose.get('head_location'):
            data.append(head_pose_data)
        for head_pose_data in head_pose.get('head_rotation'):
            data.append(head_pose_data)

        # getting all AU_XX_r values
        for au_i_data in au_i:
            data.append(au_i_data)

        # getting AU_28_c value
        data.append(au_p[len(au_p) - 2] * 1)  # *1 for getting 0/1 value and not True/False
        return data

    def format_eng_out(self, timestamp, eng_data=None, eng_val=None):
        """
            adds frame_number, timestamp and eng_val to eng_data end prepare to output datas
        """
        keys_arr = OF_const.HEADER_ARR.copy()
        # keys_arr.append('eng_val')
        eng_out = {}
        if eng_data is None:
            frame_key = keys_arr.pop(0)
            confidence_key = keys_arr.pop(0)
            timestamp_key = keys_arr.pop(0)
            eng_out['eng_val'] = None
            eng_out[frame_key] = self
            eng_out[confidence_key] = None
            eng_out[timestamp_key] = timestamp
            for i, key in enumerate(keys_arr):
                eng_out[key] = None
        else:
            eng_out['eng_val'] = eng_val
            for i, key in enumerate(keys_arr):
                eng_out[key] = float(eng_data[i])
        return eng_out
