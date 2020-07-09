function linkify(text) {
    var urlRegex =/(\b(https?|ftp|file):\/\/[-A-Z0-9+&@#\/%?=~_|!:,.;]*[-A-Z0-9+&@#\/%=~_|])/ig;
    return text.replace(urlRegex, function(url) {
        return '<a href="' + url + '" target="_blank">' + url + '</a>';
    });
}

$(document).ready(function () {
  const namespace = '/chat';

  // Connect to the Socket.IO server.
  // The connection URL has the following format, **relative to the current page**:
  // http[s]://<domain>:<port>[/<namespace>]
  // TODO: update this
  const socket = io(namespace);

  // Event handler for new connections.
  // The callback function is invoked when a connection with the
  // server is established.
  socket.on('connect', function () {
    socket.emit('chat_connect_event', { data: 'Client connected!' });
  });

  // Event handler for server sent data.
  // The callback function is invoked whenever the server emits data
  // to the client. The data is then displayed in the "Received"
  // section of the page.
  socket.on('my_response', function (msg, cb) {
    let messageFeed = document.getElementById("message-feed")
    let message = document.createElement("li");
    message.style = "margin:0 0 10px 0;"
    if (!msg.username) {
      msg.username = 'Dover'
    }
    let msg_epoch = parseInt(msg.timestamp);
    if (!msg_epoch) {
      msg_epoch = Date.now();
    }
    const msg_time = new Date(msg_epoch).toLocaleString('en-US')
    const msg_data = linkify(msg.data);
    message.innerHTML = '<b>' + msg.username + '@' + msg_time +
    ': </b><br/>' + msg_data + '<br/>';
    messageFeed.append(message);
    // Auto scroll to the bottom when new message comes in
    messageFeed.scrollIntoView(false)
    if (cb) cb();
  });

  // Handlers for the different forms in the page.
  // These accept data from the user and send it to the server in a
  // variety of ways
  $('form#broadcast').submit(function (event) {
    socket.emit(
      'broadcast_event', {
      data: $('#broadcast_data').val(),
      username: $('#username_data').val() || 'test_user'
    }
    );
    // Click send clears the textarea
    $('#broadcast_data').val('')
    return false;
  });
  $('form#disconnect').submit(function (event) {
    socket.emit('disconnect');
    return false;
  });

  // Enter as send
  function submitOnEnter(event) {
    if (event.which === 13) {
      event.target.form.dispatchEvent(new Event("submit", { cancelable: true }));
      event.preventDefault(); // Prevents the addition of a new line in the text field (not needed in a lot of cases)
    }
  }

  document
    .getElementById("broadcast_data")
    .addEventListener("keypress", submitOnEnter);
});