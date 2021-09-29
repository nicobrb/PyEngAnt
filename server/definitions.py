'''

Util const file for correct address the requires modules

'''

OPENFACEAPI_HOST = "https://www.intintlab.uniba.it/openface"# "http://127.0.0.1:8081" # 172.18.0.2
OPENFACEAPI_SESSION_ENDPOINT = "" #"/image/Session"
OPENFACEAPI_GETDATA_ENDPOINT = "/image/GetData"

OPENFACEAPI_SESSION_SECURE_CODE = "" #"qwertyuiop123456789"
OPENFACEAPI_SESSION_SECURE_CODE_JSON_PARAM = ("secure_code", OPENFACEAPI_SESSION_SECURE_CODE)

ENGRECAPI_HOST = "https://www.intintlab.uniba.it/engagement-api"#"http://127.0.0.1:8082/engrec/EngRecApi/1.0.0" # 172.18.0.3
ENGRECAPI_ENGAGEMENT_ENDPOINT = "" #"/engagement"