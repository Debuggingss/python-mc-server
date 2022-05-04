from io import BytesIO
from PIL import Image, ImageDraw
import socket
import struct
import base64
import json

# Server Host and port
HOST = "127.0.0.1"
PORT = 25565


# Taken from https://gist.github.com/ewized/97814f57ac85af7128bf
def unpack_varint(sock):
    data = 0
    for i in range(5):
        ordinal = sock.recv(1)

        if len(ordinal) == 0:
            break

        byte = ord(ordinal)
        data |= (byte & 0x7F) << 7 * i

        if not byte & 0x80:
            break

    return data


# Taken from https://gist.github.com/ewized/97814f57ac85af7128bf
def pack_varint(data):
    ordinal = b''

    while True:
        byte = data & 0x7F
        data >>= 7
        ordinal += struct.pack('B', byte | (0x80 if data > 0 else 0))

        if data == 0:
            break

    return ordinal


# Packs data with it's length in front of it
def pack_data(d):
    return pack_varint(len(d)) + d


# Ping Response
def get_ping(description, favicon, version_name="1.8.9", version_protocol=47, players=None, maxp=0, onlinep=0):
    if players is None:
        players = []

    sample = []

    for player in players:
        sample.append({
            "name": player,
            "id": "00000000-0000-0000-0000-000000000000"
        })

    resp = {
        "version": {
            "name": version_name,
            "protocol": version_protocol
        },
        "players": {
            "max": maxp,
            "online": onlinep,
            "sample": sample
        },
        "description": {
            "text": description
        },
        "favicon": f"data:image/png;base64,{favicon}"
    }

    # Directory -> JSON -> bytes
    return bytes(json.dumps(resp), "utf8")


# Kick Reason
def get_reason(reason):
    resp = {
        "text": reason
    }

    # Directory -> JSON -> bytes
    return bytes(json.dumps(resp), "utf8")


pingcount = 0

while True:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind((HOST, PORT))
        s.listen()
        c, addr = s.accept()

        with c:
            print(f"Connection from {addr}.")

            packet_length = unpack_varint(c)  # Packet Length
            packet_id = unpack_varint(c)  # Packet ID

            print(f"{addr} > {packet_id}")

            if packet_id == 0:
                protocol_version = unpack_varint(c)  # Protcol Version
                server_address_length = unpack_varint(c)  # Server Address Length
                server_address = c.recv(server_address_length)  # Server Address
                server_port = c.recv(2)  # Server port
                next_state = unpack_varint(c)  # Next State
                c.recv(1024)  # Remaining Useless Data

                if next_state == 1:
                    pingcount += 1

                    # Open the icon.png image and write the current ping count on it
                    img = Image.open("icon.png")
                    draw = ImageDraw.Draw(img)
                    draw.text((10, 10), str(pingcount), (255, 255, 255))
                    img = img.resize((64, 64))

                    # Save the image into a buffer so we can turn it into a base64 string
                    buffer = BytesIO()
                    img.save(buffer, format="PNG")
                    img_str = base64.b64encode(buffer.getvalue())

                    # Create a response json with the given parameters
                    res = get_ping(
                        f"§aHello World!\n§7I've been pinged §b{str(pingcount)} §7times.",
                        img_str.decode('utf8'),
                        "1.8.9",
                        47,
                        [
                            "This is the player list",
                            "You can put anything here",
                            "§cColor codes work!"
                        ],
                        0,
                        0
                    )

                    # Create the ping packet (ID 0)
                    data = b''
                    data += b'\x00'
                    data += pack_data(res)
                    data = pack_data(data)

                    # Send the packet to the client
                    c.sendall(data + b'\x00')

                    # Send the same ping packet (ID 1) back to the client
                    c.sendall(c.recv(1024))

                if next_state == 2:
                    # Make the disconnect packet
                    reason = get_reason("§cGood bye, world!\n§7You are unable to join this server! :(")

                    # Create the disconnect packet (ID 0)
                    data = b''
                    data += b'\x00'
                    data += pack_data(reason)
                    data = pack_data(data)

                    # Send the packet to the client
                    c.sendall(data + b'\x00')

            # Close the socket
            c.close()
