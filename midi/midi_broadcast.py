import rtmidi
import zmq
import threading

def forward_messages(pull_socket, pub_socket):
    while True:
        try:
            msg = pull_socket.recv_pyobj()
            pub_socket.send_pyobj(msg)
        except zmq.ZMQError:
            pass

# Set up PUB socket for MIDI messages
pub_context = zmq.Context()
pub_socket = pub_context.socket(zmq.PUB)
pub_socket.bind("tcp://*:5555")

# Set up PULL socket for file change messages
pull_context = zmq.Context()
pull_socket = pull_context.socket(zmq.PULL)
pull_socket.bind("tcp://*:5556")

# Start message forwarding in a separate thread
forward_thread = threading.Thread(target=forward_messages, args=(pull_socket, pub_socket))
forward_thread.daemon = True
forward_thread.start()

# Set up MIDI input
midi_in = rtmidi.MidiIn()
if midi_in.get_port_count() > 0:
    midi_in.open_port(0)
    print('MIDI input listening...')
    while True:
        msg = midi_in.get_message()
        if msg and msg[0][0] == 144:  # Note on/off message
            print(msg)
            pub_socket.send_pyobj(msg)