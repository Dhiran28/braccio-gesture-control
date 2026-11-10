---
tags: [concept, network, udp]
---
# UDP Networking

## What UDP is
**UDP** sends small messages ("datagrams") from one computer to another address + port. There's no connection set-up and no delivery guarantee. That sounds bad, but for live control it's ideal:
- **Fast**: no waiting for acknowledgements.
- A lost packet doesn't matter: a newer one arrives 40 ms later anyway.
- The alternative, TCP, would *re-send* old lost positions, causing lag and stutter.

## Our protocol
| Item | Value |
|---|---|
| To | `192.168.1.100` (the UNO R4 WiFi), port **5005** |
| Rate | 25 packets per second (`SEND_HZ`) |
| Content | ASCII text: `base,shoulder,elbow,wristUpDown,wristTwist,gripper` |
| Example | `90,82,21,12,90,20` |

## Sending, in Python
```python
import socket
sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)   # AF_INET = IPv4, SOCK_DGRAM = UDP
sock.sendto(b"90,90,90,90,90,20", ("192.168.1.100", 5005))
```
That's the whole `Sender` class in [[hand_to_braccio.py]].

## Receiving, on the Arduino (`braccio_udp.ino`, from the Quest project)
In outline: `WiFiUDP.parsePacket()` → read the text → split at commas → clamp each value to its limits → move the servos gradually (a small step every few ms, so motion is smooth even if packets are uneven).

## Why keep sending when nothing changes?
The arm gets a steady "stay here" stream. If the arm restarts or a packet is lost, it gets the right pose again within 40 ms.

## Try it yourself
```bash
python3 -c "import socket; socket.socket(2,2).sendto(b'90,90,90,90,90,20', ('192.168.1.100',5005))"
```
(`2,2` = `AF_INET, SOCK_DGRAM`.) This sends the arm to candle once. That's what [[joint_test.py]] does in a loop.

> [!warning] One sender at a time
> The Quest app also sends to port 5005. Two senders = two sets of commands = a twitching arm.
