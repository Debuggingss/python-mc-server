"""
 A simple server to check your IP address and account information.
 Useful for double checking your VPN before joining sketchy servers.
 This is useless if it's ran locally obviously...

 Built-in ratelimiter to avoid spamming the APIs.
"""

from io import BytesIO
from PIL import Image
from uuid import UUID
import requests
import socket
import struct
import base64
import time
import json

HOST = "127.0.0.1"
PORT = 25565
RATELIMIT = 5

img = Image.open("icon.png")
img = img.resize((64, 64))
buffer = BytesIO()
img.save(buffer, format="PNG")
img_str = base64.b64encode(buffer.getvalue())
favicon = img_str.decode('utf8')

PROFILES_URL = "https://api.mojang.com/users/profiles/minecraft/"
IP_API_URL = "http://ip-api.com/json/"

ratelimit = {}


def get_uuid(username):
    r = requests.get(PROFILES_URL + username)
    json_data = r.json()

    if "id" in json_data:
        return UUID(hex=json_data["id"])
    else:
        return None


def get_ip_info(ip):
    r = requests.get(IP_API_URL + ip)
    json_data = r.json()

    if "status" in json_data:
        return json_data
    else:
        return {}


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


def pack_varint(data):
    ordinal = b''

    while True:
        byte = data & 0x7F
        data >>= 7
        ordinal += struct.pack('B', byte | (0x80 if data > 0 else 0))

        if data == 0:
            break

    return ordinal


def pack_data(d):
    return pack_varint(len(d)) + d


def get_ping(description, favicon, version_protocol=47, version_name="1.8.9", players=None, maxp=0, onlinep=0):
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

    return bytes(json.dumps(resp), "utf8")


def get_reason(reason):
    resp = {
        "text": reason
    }

    return bytes(json.dumps(resp), "utf8")


while True:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind((HOST, PORT))
        s.listen()
        c, addr = s.accept()

        with c:
            ip = addr[0]
            print(f"Connection from {ip}.")

            unpack_varint(c)  # Packet Length
            packet_id = unpack_varint(c)

            if packet_id == 0:
                protocol_version = unpack_varint(c)
                server_address_length = unpack_varint(c)
                c.recv(server_address_length)  # Server Address
                c.recv(2)  # Server Port
                next_state = unpack_varint(c)

                if next_state == 1:
                    res = get_ping(
                        f"§7Check client IP on login.",
                        favicon,
                        protocol_version,
                        "1.8 - 1.18",
                        [
                            "§8IPCheck Server",
                            "§7Log into the server to",
                            "§7check your IP address and",
                            "§7account information."
                        ]
                    )

                    data = b''
                    data += b'\x00'
                    data += pack_data(res)
                    data = pack_data(data)

                    c.sendall(data + b'\x00')

                    # Request packet with no data
                    unpack_varint(c)
                    unpack_varint(c)

                    c.sendall(c.recv(1024))

                elif next_state == 2:
                    now = time.time()

                    if ip in ratelimit and (now - ratelimit[ip]) < RATELIMIT:
                        data = b''
                        data += b'\x00'
                        data += pack_data(get_reason(
                            f"§cYou are being ratelimited!\n"
                            f"§cTry again in {round(RATELIMIT - (now - ratelimit[ip]), 1)} seconds."
                        ))
                        data = pack_data(data)

                        c.sendall(data + b'\x00')
                        time.sleep(1)
                        continue

                    ratelimit[ip] = now

                    unpack_varint(c)  # Packet Length
                    unpack_varint(c)  # Packet ID

                    username_length = unpack_varint(c)
                    username = c.recv(username_length).decode("utf8")
                    uuid = get_uuid(username) or "§cError"

                    ipinfo = get_ip_info(ip)

                    country = ipinfo.get("country") or "§cError"
                    city = ipinfo.get("city") or "§cError"
                    isp = ipinfo.get("isp") or "§cError"

                    reason = get_reason(
                        f"§8Network\n"
                        f"§7IP: §f{ip}\n"
                        f"§7Country: §f{country}\n"
                        f"§7City: §f{city}\n"
                        f"§7ISP: §f{isp}\n"
                        f"\n§8Account\n"
                        f"§7Username: §f{username}\n"
                        f"§7UUID: §f{uuid}"
                    )

                    data = b''
                    data += b'\x00'
                    data += pack_data(reason)
                    data = pack_data(data)

                    c.sendall(data + b'\x00')

                    print(f"{username} ({uuid}) has logged in from {ip}.")
