from sys import stdout
import logging
from flask import Flask, render_template, session, request
from flask_session import Session
from flask_socketio import SocketIO, emit, disconnect
from werkzeug.middleware.proxy_fix import ProxyFix
import cv2
import numpy as np
import base64
import requests as r
from time import sleep
import sys

from eng_session_manager import EngSessionManager

# parameters for eventlet fixtures
import eventlet

eventlet.monkey_patch()

# initialization params for Flask Framework
app = Flask(__name__)
app.logger.addHandler(logging.StreamHandler(stdout))
app.config['SECRET_KEY'] = 'secret!'
app.config['DEBUG'] = True
app.config['SESSION_TYPE'] = 'filesystem'
Session(app)
socketio = SocketIO(app, manage_session=False, ping_timeout=30, ping_interval=15, cors_allowed_origins='*')
app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_host=1)  # for proxy testing

ENCODING = "utf-8"
session_manager = EngSessionManager()  # initialize an  EngSessionManager


def check_session_id(fps):
    with app.test_request_context('/session'):
        openface_id = session.get("openface_id")
        if openface_id is None:
            try:
                # try to create a session 
                session_id = session_manager.create_eng_session(fps)

                # if fails returns -1 to disconnect a client
            except r.ConnectionError as e:
                print(f"ConnectionError: ", e)
                return -1
            except r.RequestException as e:
                print(f"RequestError: ", e)
                return -1
            except IOError as io_exception:
                print(f"I/O error:", io_exception)
                return -1
            except ValueError as e:
                print(e)
                return -1
            except RuntimeError as e:
                print(e)
                return -1
            except Exception:
                print("Unexpected error:", sys.exc_info()[0])
                raise
            if session_id is None:
                app.logger.warn(
                    f"Session not created. Check OpenFaceApi Webserver is up and running. aborting connection.")
                return -1
            session["openface_id"] = session_id
            app.logger.info(f"Session n. {session_id} created")
            return session_id
        else:
            app.logger.info(f"Already have session_id:{openface_id}")
            eng_session = session_manager.get_session(openface_id)
            if eng_session is not None:
                if eng_session.is_valid():
                    app.logger.info(f"Session with session_id:{openface_id} valid.")
                else:
                    app.logger.warn(f"Session with session_id:{openface_id} not valid. aborting connection.")
                    session["openface_id"] = None
                    session_manager.remove_session(openface_id)
                    return -1
            else:
                app.logger.warn(f"Session with session_id:{openface_id} no longer exist. aborting connection.")
                session["openface_id"] = None
                return -1


@socketio.on('input_image', namespace='/session')
def analyze_process(input):
    image = input["image"].split(",")[1]
    curr_time = input["current_time"]
    sessions = input["session_id"]
    image_data = image.encode(ENCODING)
    buffer = base64.b64decode(image_data)
    cv2_img = cv2.imdecode(np.frombuffer(buffer, dtype=np.uint8), flags=cv2.IMREAD_COLOR)
    cv2_img = cv2.putText(cv2_img,
                          str.format("time:{}", curr_time),
                          (5, 40),
                          cv2.FONT_HERSHEY_PLAIN, 1, (0, 255, 000),  # green color in BGR
                          thickness=1, lineType=1)
    retval, buffer = cv2.imencode('.jpg', cv2_img, [int(cv2.IMWRITE_JPEG_QUALITY),
                                                    80])  # [int(cv2.IMWRITE_JPEG_QUALITY), 50] for reduce quality image
    b = base64.b64encode(buffer)
    b = b.decode(ENCODING)
    image_data = b
    if sessions is None:
        return
    eng_session = session_manager.get_session(sessions)
    if eng_session is None:
        # check_session_id()
        return
    if not eng_session.is_valid():
        message = eng_session.get_message()
        emit("log_message", "ERROR: Session is not vaild, deleting session. Reason: " + message)
        disconnect()
        app.logger.info("client disconnected")
        try:
            session_manager.remove_session(eng_session.get_session_id())
        except r.ConnectionError as e:
            print(f"ConnectionError: ", e)
            # emit("log_message","ERROR: Deleting session failed. Check OpenFaceApi is running.")
        except r.RequestException as e:
            print(f"RequestError: ", e)
            # emit("log_message","ERROR: Deleting session failed. Check OpenFaceApi is running.")

    eng_session.addFrame(image_data)
    emit("output_data", eng_session.get_output_data())

    # status_code, ret_img, ret_eng_data = eng_session.analyze_frame(image_data)
    # if(status_code == 200):
    #    emit('output_data', {'image_data': ret_img,'eng_data':ret_eng_data}, namespace='/session')
    # else:
    #    session["openface_id"] = None
    #    disconnect()


@socketio.on('delete_session', namespace='/session')
def delete_session(input):
    openface_id = input["session_id"]
    ret = session_manager.remove_session(openface_id)
    if ret:
        app.logger.info(f"Session n. {openface_id} deleted")
    else:
        app.logger.error(f"Session n. {openface_id} not deleted")


@socketio.on('client_disconnect_request', namespace='/session')
def disconnect_client():
    sess_data = session.copy()
    session["openface_id"] = None
    emit("log_message", "INFO: Ended streaming. Closing connection.")
    disconnect()
    app.logger.info("client disconnected")
    eng_session = session_manager.get_session(sess_data['openface_id'])
    if not eng_session is None:
        eng_session.flush_data()
        try:
            session_manager.remove_session(sess_data['openface_id'])
        except r.ConnectionError as e:
            print(f"ConnectionError: ", e)
            # emit("log_message","ERROR: Ending session failed. Check OpenFaceApi is running.")
        except r.RequestException as e:
            # emit("log_message","ERROR: Ending session failed. Check OpenFaceApi is running.")
            print(f"RequestError: ", e)
    else:
        app.logger.error(f" Trying to delete session: {sess_data['openface_id']} but not retreived.")


@socketio.on('client_video_end_disconnect_request', namespace='/session')
def disconnect_client_video_end():
    sess_data = session.copy()
    eng_session = session_manager.get_session(sess_data['openface_id'])
    if not eng_session is None:
        i = 0
        while len(eng_session.frame_to_process) > 0 or len(eng_session.data_to_output) > 0:
            sleep(10)
            print(f"session {sess_data['openface_id']}: video ended but frame list not empty.")
            emit('log_message', "WARNING: video ended but analysis is going to end.")
            i += 1
        session["openface_id"] = None
        emit("log_message", "INFO: Ended streaming. Closing connection.")
        disconnect()
        app.logger.info("client disconnected")
        print(f"Session:{sess_data['openface_id']} deleted.")
        try:
            session_manager.remove_session(sess_data['openface_id'])
        except r.ConnectionError as e:
            print(f"ConnectionError: ", e)
            emit("log_message", "ERROR: Ending session failed. Check OpenFaceApi is running.")
        except r.RequestException as e:
            print(f"RequestError: ", e)
            emit("log_message", "ERROR: Ending session failed. Check OpenFaceApi is running.")
    else:
        app.logger.error(f"session not retreived with openface_id:{sess_data['openface_id']}")


@socketio.on('disconnect', namespace='/session')
def disconnect_client():
    app.logger.info("client disconnected. Sid:", request.sid)


@socketio.on('connect', namespace='/session')
def test_connect():
    app.logger.info("client disconnected. Sid:", request.sid)


@socketio.on('check_session_id', namespace='/session')
def start_eng_analysis(data):
    id = check_session_id(int(data["fps"]))
    if id > 0:
        print("Starting analysis for session: ", id)
        session["openface_id"] = id
        emit('check_session_id_response', {'session_id': id, 'input_type': data["input_type"]})
    else:
        session["openface_id"] = None
        emit('log_message', "ERROR: Session not created. Check OpenFaceApi is running.")
        disconnect()


@app.route('/')
def index():
    """Video streaming home page."""
    return render_template('index.html')


if __name__ == '__main__':
    socketio.run(app, debug=True)
