from flask import Flask, render_template, request, redirect, url_for, flash
from flask_socketio import SocketIO, join_room, leave_room, send

app = Flask(__name__)
app.config['SECRET_KEY'] = 'secret!'
app.config['DEBUG'] = True
socketio = SocketIO(app)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/room/<room_name>')
def room(room_name):
    return render_template('room.html', room_name=room_name)

@socketio.on('join')
def on_join(data):
    room = data['room']
    join_room(room)
    send(f"{data['username']} has joined {room}.", room=room)

@socketio.on('leave')
def on_leave(data):
    room = data['room']
    leave_room(room)
    send(f"{data['username']} has left {room}.", room=room)

@socketio.on('message')
def handle_message(data):
    send(data, room=data['room'])

if __name__ == '__main__':
    socketio.run(app, debug=True)