$(document).ready(function() {
    var socket = io.connect(location.protocol + '//' + document.domain + ':' + location.port);
    var room = '{{ room_name }}';

    socket.on('connect',function() {
        socket.emit('join', {'room': room, 'username': prompt('Enter your username:')});
    });

    socket.on('message', function(data) {
        $('#messages').append($('<p>').text(data));
    });

    $('#message-form').submit(function(event) {
        event.preventDefault();
        var message = $('#message').val();
        socket.emit('message', {'room': room, 'message': message});
        $('#message').val('');
    });

    $('#message-form button').click(function() {
        socket.emit('leave', {'room': room, 'username': $('#username').val()});
    });
});