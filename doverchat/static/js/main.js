let CURRENT_ROOM_NAME, CURRENT_ROOM_CODE, ROOM_MAP;

function linkify(text) {
    var urlRegex =/(\b(https?|ftp|file):\/\/[-A-Z0-9+&@#\/%?=~_|!:,.;]*[-A-Z0-9+&@#\/%=~_|])/ig;
    return text.replace(urlRegex, function(url) {
        return '<a href="' + url + '" target="_blank">' + url + '</a>';
    });
}

function _build_message(msg) {
  let message = document.createElement("li");
  message.style = "margin:0 0 10px 0;"
  if (!msg.user_screen_name) {
    msg.user_screen_name = 'Dover'
  }
  let msg_epoch = parseInt(msg.created_at);
  if (!msg_epoch) {
    msg_epoch = Date.now();
  }
  const msg_time = new Date(msg_epoch).toLocaleString('en-US')
  const msg_data = linkify(msg.message_text);
  message.innerHTML = '<b>' + msg.user_screen_name +
    '</b>  <span style="font-size:0.8em">@' + msg_time +
    '</span> : <br/>' + msg_data + '<br/>';
  return message;
}

async function getRoomInfo() {
  const response = await fetch(`/userrooms`);
  return response.json();
}

async function getRoomLastMessages(room_code) {
  const response = await fetch(`/last-msgs?room_code=${room_code}`);
  return response.json();
}


$(document).ready(function () {
  const namespace = '/';

  // Connect to the Socket.IO server.
  // The connection URL has the following format, **relative to the current page**:
  // http[s]://<domain>:<port>[/<namespace>]
  const socket = io(namespace);

  function switchRoom(room_code, room_name) {
    socket.emit('leave', {room_code: CURRENT_ROOM_CODE});
    $('#message-feed').empty();
    console.log(`Leaving ${CURRENT_ROOM_NAME} and joining ${room_name}`);
    CURRENT_ROOM_NAME = room_name;
    CURRENT_ROOM_CODE = room_code;
    window.name = CURRENT_ROOM_CODE;
    $('#room-banner').text(`当前房间：${CURRENT_ROOM_NAME}`);
    socket.emit('join', {room_code: CURRENT_ROOM_CODE});
    // load last 20 messages in this room from db
    getRoomLastMessages(CURRENT_ROOM_CODE).then(lastMessages => {
      let messageFeed = document.getElementById("message-feed");
      for (const msg of lastMessages) {
        let message = _build_message(msg);
        messageFeed.append(message);
      }
      // Auto scroll to the bottom when new message comes in
      messageFeed.scrollIntoView(false);
    })
  }


  getRoomInfo().then(userrooms => {
    // Construct room_map
    const room_map = {};
    for (const room_pair of userrooms) {
      let room_code = room_pair[0];
      let room_name = room_pair[1];
      room_map[room_code] = room_name;
    }
    if (!window.name) {
      [CURRENT_ROOM_CODE, CURRENT_ROOM_NAME] = userrooms[0];
      window.name = CURRENT_ROOM_CODE;
    } else {
      CURRENT_ROOM_CODE = window.name;
      CURRENT_ROOM_NAME = room_map[CURRENT_ROOM_CODE];
    }
    $('#room-banner').text(`当前房间：${CURRENT_ROOM_NAME}`);
    socket.emit('join', {room_code: CURRENT_ROOM_NAME});

    for (const dropdownRoom of userrooms) {
      const dropdownRoomElement = document.createElement('a');
      dropdownRoomElement.className = "dropdown-item";
      dropdownRoomElement.innerHTML = dropdownRoom[1];
      $('#dropdown-rooms').append(dropdownRoomElement);
      dropdownRoomElement.addEventListener(
        'click', () => switchRoom(dropdownRoom[0], dropdownRoom[1])
      );
    }

    getRoomLastMessages(CURRENT_ROOM_CODE).then(lastMessages => {
      let messageFeed = document.getElementById("message-feed");
      for (const msg of lastMessages) {
        let message = _build_message(msg);
        messageFeed.append(message);
      }
      // Auto scroll to the bottom when new message comes in
      messageFeed.scrollIntoView(false);
    })
  });


  // Event handler for new connections.
  // The callback function is invoked when a connection with the
  // server is established.
  socket.on('connect', function () {
    console.log('Connected!')
  });

  // Event handler for server sent data.
  // The callback function is invoked whenever the server emits data
  // to the client. The data is then displayed in the "Received"
  // section of the page.
  socket.on('my_response', function (msg, cb) {
    let messageFeed = document.getElementById("message-feed")
    let message = _build_message(msg);
    messageFeed.append(message);
    // Auto scroll to the bottom when new message comes in
    messageFeed.scrollIntoView(false);
    if (cb) cb();
  });

  // Handlers for the different forms in the page.
  // These accept data from the user and send it to the server in a
  // variety of ways
  $('form#broadcast').submit(function (event) {
    const message = $('#broadcast_data').val();
    if (message !== "") {
      socket.emit(
        'broadcast_event', {
        message_text: message,
        room_code: CURRENT_ROOM_CODE
      });
      // Click send clears the textarea
      $('#broadcast_data').val('');
    }
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
