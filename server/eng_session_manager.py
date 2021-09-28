from flask import session
from flask_socketio import Namespace, emit, disconnect
from flask_session import Session
from eng_session import EngSession
import requests as r
import sys
import definitions


class EngSessionManager(object):
    
    def __init__(self):
        self.manager = {}
    
    def create_eng_session(self, fps):
        try:
            response = r.get(url=definitions.OPENFACEAPI_HOST+definitions.OPENFACEAPI_SESSION_ENDPOINT,
                             params=[definitions.OPENFACEAPI_SESSION_SECURE_CODE_JSON_PARAM],
                             verify=False)
            if(response.status_code ==200):
                print(response.content)
                openface_id = response.json()["session_id"]
                session = EngSession(openface_id, fps)
                self.manager[openface_id] = session
                return openface_id
            else:
                raise r.RequestException(response.json()["message"])
        except r.ConnectionError as e:
            raise
        except r.RequestException as e:
            raise
        except IOError as io_exception:
            raise
        except ValueError as e:
            raise
        except RuntimeError as e:
            raise
        except:
            raise
    
    def get_session(self, openface_id):
        return self.manager.get(openface_id)
    
    def remove_session(self, session_id):
        ret = False
        eng_session = self.manager.get(session_id)
        if eng_session:
            self.manager.pop(session_id)
            ret = True
            try:
                response = r.delete(url=definitions.OPENFACEAPI_HOST+definitions.OPENFACEAPI_SESSION_ENDPOINT,
                                    json={"session_id":eng_session.get_session_id()},
                                    params=[definitions.OPENFACEAPI_SESSION_SECURE_CODE_JSON_PARAM],
                                    verify=False)
            except r.ConnectionError as e:
                raise
            except r.RequestException as e:
                raise
            except IOError as io_exception:
                raise
            except ValueError as e:
                raise
            except RuntimeError as e:
                raise
            except:
                raise
        return ret

    
    