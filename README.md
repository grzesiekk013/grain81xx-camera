# GRAIN 81XX CAMERA - BLOW 78-701

![BlowCamera](images/image.png)

This IP camera originally relied on an outdated P2P server (`P2PICAMERA.COM`), which is now permanently down.

The goal of this project is to rescue the camera from e-waste and turn it into a simple, reliable, local-only IP camera-free of cloud dependencies-with working PTZ (Pan-Tilt-Zoom) controls and a live video stream.

To achieve this, I had to analyze the system processes and disassemble parts of the original firmware to reproduce the hardware controls.

---

## Getting Root Shell

1. *Connect via UART:* Solder jumper wires to the onboard UART (COM) header and connect it to a USB-to-TTL adapter.
2. *Bypass the Watchdog:* The system runs a hardware watchdog (`cpe-wdt.ko`) with a 15-second timeout. If you stop the main application with `Ctrl+C` after it has fully started, the watchdog will reboot the device. However, if you press `Ctrl+C` *very early* during boot, the watchdog never starts, giving you a stable root shell.
3. *Crack the Root Password:* Read `/etc/passwd` and `/etc/shadow` to extract the root password hash:
   - *DES Hash:* `N.lbMktxdQ76A`
   - *Cracked Password (via `hashcat`):* `GM8182`
4. *Telnet Access:* Port `23` (Telnet) is open by default and requires the root password obtained above.

---

## Hardware & Reverse Engineering Notes

- *PTZ & IR Control:* The pan and tilt mechanisms use stepper motors driven directly via GPIO, with GPIO limit switches detecting the start and end positions. I wrote `libs/ptz_test.c` (with AI assistance) to control motor movement and the IR LEDs.
- *Video Capture:* To access the video pipeline directly, the manufacturer's P2P streaming daemon (`nvisr`) and the watchdog (`cpe-wdt.ko`) must be disabled by overriding `boot.sh`.
- *Current Status:* `snap.c` is currently under construction.

---

## Useful Commands

Configure static IP on the camera:
```sh
ip addr add 10.0.12.215/24 dev eth0
ip link set eth0 up
```

Transfer binaries using `netcat`:
```sh
# On the camera:
nc -l -p 9010 > /tmp/snap && chmod +x /tmp/snap && ./tmp/snap
nc -l -p 9010 > /tmp/ptz_test && chmod +x /tmp/ptz_test 

# On the host machine:
nc -N 10.0.12.215 9010 < snap
```

---

## Project Roadmap

### Done
- [x] Solder jumper wires to the UART port
- [x] Capture and analyze U-Boot logs
- [x] Extract `/etc/shadow` and crack the DES root password (`GM8182`) with `hashcat`
- [x] Log in via Telnet
- [x] Override `boot.sh` (sys/new_mnt_motd_boot.sh) to disable the manufacturer's application and watchdog
- [x] Write the PTZ & IR control library (`libs/ptz_test.c`) (using ghidra decompiler)
- [x] Capture an MJPEG frame (`snap.c`) (using ghidra decompiler)

### Web APP
![WebApp](images/web_app.png)

### To Do
- [ ] DHCP
- [ ] Get WiFi working
- [ ] Get MicroSD working
- [ ] Get Audio working (not neccesary)
- [ ] Clean up SPI Flash (remove manufacturer bloat)
- [ ] Run a lightweight HTTP MJPEG streamer
- [ ] Make wrapper for ptz_test (goto pan/tilt cords and simple pan/tilt)