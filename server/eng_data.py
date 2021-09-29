from flask import session
from flask_socketio import Namespace, emit, disconnect
from flask_session import Session
from eng_session import EngSession
import requests as r
import sys
import definitions


class EngData(object):
    
    def __init__(self, frame, timestamp, confidence = None, gaze = None, head_pose = None, aus_i = None, aus_p = None, eng_val = None):
        self.frame = frame
        self.timestamp = timestamp
        self.confidence = confidence
        self.eng_val = eng_val

    
    