'''
Gunicorn configuration file

'''

#define here the address binded to WebSocket
HOST = "0.0.0.0"
#define here the port from which WebSocket will be reachable
PORT = "8083"

# CONFIGURATION PARAMS
bind = HOST + ":"+ PORT
workers = 1