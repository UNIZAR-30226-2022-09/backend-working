from app import app
from flask import request, session
from flask_socketio import SocketIO, join_room,leave_room, emit
socketio = SocketIO(app, cors_allowed_origins="*")
from datetime import datetime
from app import db, Chat

@socketio.on('message')
def chat(message):
    
    print(message)
    print(request.sid)
    
    created_at = datetime.now()
    nick = message['user']
    mensaje = message['message']
    room = message['sala']
    
    chat_message = Chat(nick=nick, created_at = created_at, message=mensaje, room=room)
    db.session.add(chat_message)
    db.session.commit()

    print(room)
    emit('message',(mensaje,nick), broadcast=True, to=room)

@socketio.on('disconnect')
def disconnect():
    print("User left to Socket")

@socketio.on('connect')
def disconnect():
    emit('connect',"Conectado chavalin")
    print("User Added to Socket")

# Funcion para almacenar por cada Usuario un SocketID único en esa sesion
# que cambiará a traves de las diferentes sesiones que pueda tener

@socketio.on('join')
def on_join(data):
    join_room(data['room'])
    emit('join' , 'A user has entered the room.', to=data['room'])
    print(type(data['room']))
    addRoomSession(data['room'])

def addRoomSession(room):
    if 'rooms' not in session:
        session['rooms'] = []

    rooms = session['rooms']
    rooms.append(room)
    session['rooms'] = rooms
    print(session['rooms'])

@socketio.on('leave')
def on_leave(data):
    leave_room(data['room'])
    emit('leave' , 'A user has left the room.', to=data['room'])    
    print(type(data['room']))
    removeRoomSession(data['room'])

def removeRoomSession(room):

    rooms = session['rooms']

    rooms.remove(room)
    session['rooms'] = rooms
    print('salas activas: {}'.format(session['rooms']))


