class EngData(object):

    def __init__(self, frame, timestamp, confidence=None, gaze=None, head_pose=None, aus_i=None, aus_p=None,
                 eng_val=None):
        self.frame = frame
        self.timestamp = timestamp
        self.confidence = confidence
        self.eng_val = eng_val
