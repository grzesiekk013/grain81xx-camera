# GRAIN 81XX CAMERA - BLOW 78-701

![BlowCameraBanner](images/grain81xx-banner.png)

This IP camera originally relied on an outdated P2P server (`P2PICAMERA.COM`), which is now permanently down.

The goal of this project is to rescue the camera from e-waste and turn it into a simple, reliable, local-only IP camera free of cloud dependencies with working PTZ (Pan-Tilt-Zoom) / IR controls and a live snapshot / MJPEG-style web stream.

To achieve this, I analyzed the system processes and decompiled parts of the original `nvisr` firmware (using Ghidra) to reproduce the hardware controls without relying on `nvisr`.

## Hardware Specifications

| Component | Details |
| :--- | :--- |
| **SoC / CPU** | Grain Media GM8125 540MHz |
| **RAM** | 128 MB DDR2 (Samsung) 80MHz |
| **Storage** | 16 MB SPI Flash (3MB User space) + MicroSD card slot |
| **Camera Sensor** | 3 MPx sensor - I get around 0.7 FPS |
| **Networking** | 10/100 Mbps Ethernet + BL-3070-3B WiFi module |
| **PTZ Actuators** | 2x stepper motors (Pan & Tilt) with GPIO limit switches |
| **I/O & Peripherals** | 1x alarm relay, audio out, physical reset button, DC power jack |
| **OS** | Linux A320D 2.6.28 #1285 PREEMPT Thu Dec 25 17:19:45 CST 2014 armv5tel GNU/Linux |
| **GCC** | gcc version 4.4.0 (Faraday C/C++ Compiler Rlease 20100325) |
---

## Repository Structure

```text
grain81xx-camera/
├── bins/           # Precompiled ARM binaries (ptz_test, snap)
├── decompile/      # Ghidra decompilation screenshots and reverse-engineering notes
├── flash_dump/     # Full SPI Flash partition dumps (mtd0.bin - mtd5.bin)
├── images/         # Hardware photos, captured sample frames, and web UI preview
├── libs/           # C source code for hardware tools (ptz_test.c, snap.c)
├── sys/            # Original and modified boot scripts + MTD backup (mtd1_backup.bin)
├── tests/          # Experimental scripts and test artifacts
├── web_app/        # Persistent web interface & CGI handlers (index.html, ptz.html, cgi-bin/)
└── passwd          # Extracted system user database
```

---

### Instruction

#### Variant A: UART Serial Access
1. Solder a USB-to-TTL UART adapter to the PCB serial port (see `images/`, connecting `VCC` is not needed).
2. Connect to the serial port at `38400` baud, `8N1` (8 data bits, no parity, 1 stop bit), then power on the camera.

#### Variant B: Ethernet & Telnet Access
1. Connect the camera via Ethernet and check its IP address in your router dashboard.
2. Open a terminal, run `telnet <IP_ADDRESS>`, and log in as `root` with password `GM8182`.

#### Replacing `boot.sh` and Deploying Binaries
3. Watch the boot output until the application logs appear, then press `Ctrl+C` until you get a shell prompt.
4. Go to `/mnt/mtd/` (`cd /mnt/mtd/`), back up the original script (`mv boot.sh boot.sh.old`), create a new one (`touch boot.sh && chmod 777 boot.sh`), open it in `vi boot.sh`, press `A` to insert, and paste the contents of `sys/boot.sh` (or `sys/new_mnt_motd_boot.sh`). Set your WiFi `SSID` and password (`WPAPSK`) if you want WiFi enabled, then press `Esc`, type `:wq`, and run `sync` followed by `reboot`.
5. With the stock software bypassed, transfer the compiled binaries from `bins/` to `/mnt/mtd/bins` (using the `nc` transfer commands), run `sync`, reboot the camera, and test them.
6. To get microSD working make sure if it is formated in ext3, ext2, vfat, msdos or iso9660. SD should be mounted in `/mnt/sd`.

---

## Getting Root Shell & Flash Backup

1. **Connect via UART:** Solder jumper wires to the onboard UART (COM) header and connect it to a USB-to-TTL adapter.
2. **Bypass the Watchdog:** The system runs a hardware watchdog (`cpe-wdt.ko`) with a 15-second timeout. Stopping the main application after boot triggers a watchdog reboot, whereas interrupting early or omitting `cpe-wdt.ko` in `boot.sh` keeps a stable root shell.
3. **Crack the Root Password:** Read `/etc/passwd` and `/etc/shadow` (see `passwd`) to extract the root password hash:
   * **DES Hash:** `N.lbMktxdQ76A`
   * **Cracked Password (via `hashcat`):** `GM8182`
4. **Telnet Access:** Port `23` (`telnetd`) is started from `boot.sh` and accepts the root password cracked above.
5. **Backup SPI Flash:** Before modifying `/mnt/mtd`, dump all MTD partitions (`mtd0`–`mtd5`, saved in `flash_dump/` and `sys/mtd1_backup.bin`) so the stock firmware can be restored if needed.

---

## Hardware & Reverse Engineering Notes

* **PTZ & IR Control (`libs/ptz_test.c`):** Pan and tilt use stepper motors driven via `/dev/gpio0` (`ftgpio.ko`) using `ioctl` commands (`2`, `4`, `5`, `6`, `7`, `8`), with GPIO limit switches (`LEFT`, `RIGHT`, `UP`, `DOWN`) and IR outputs (`ircut`, `irled`). Standalone `ptz_test` sets pin directions explicitly (`ioctl` `2` for bank `0`, `ioctl` `6` for bank `1`, including bank `1` pin `13`), and `/mnt/mtd/boot.sh` (`sys/new_mnt_motd_boot.sh`) applies the required pinmux masks on `0x99000050`, `0x99000054`, and `0x99000058` so PTZ and IR work immediately after boot without `nvisr`.
* **Video Capture (`libs/snap.c` & `web_app/cgi-bin/snap.cgi`):** `boot.sh` loads the HM1375 / `videograph` / `dvr_enc` / `fmjpeg_drv` kernel modules without `cpe-wdt.ko` or `nvisr`. Because `snap` fails if the target output file already exists and concurrent calls can trigger `dvr_graph` / rate-control errors, `snap.cgi` writes to a unique temporary file in `/tmp/`, moves it atomically to `/tmp/snap.jpg`, and serializes access using a `/tmp/snap.lock` directory lock.
* **Persistent Web App (`web_app/`):** Static pages and CGI scripts are stored on persistent flash under `/mnt/mtd/opt/www` (`index.html`, `ptz.html`, `cgi-bin/snap.cgi`, `cgi-bin/ptz.cgi`) and served via BusyBox `httpd -h /mnt/mtd/opt/www -p 80` started from `/mnt/mtd/boot.sh`.
- **WiFi & DHCP (`ra0` / `eth0` & `/mnt/mtd/udhcpc.script`):** RT3070 (`BL-3070-3B`) loads via `rtutil3070sta.ko`, `rt3070sta.ko`, and `rtnet3070sta.ko`, associates with `iwpriv`, and gets an IP after a short `sleep` using `udhcpc -i <iface> -s /mnt/mtd/udhcpc.script -b` (since the default DHCP script did not apply the lease). Having both `eth0` and `ra0` on the same subnet (e.g. `10.0.12.0/24`) can cause routing conflicts.
- **MicroSD (`ftsdc010.ko` & `/mnt/sd`):** Loading `/lib/modules/ftsdc010.ko` exposes the SD card (`mmcblk0`, supported filesystems include `ext3`, `ext2`, `vfat`, `msdos`, `iso9660`) mounted at `/mnt/sd`. Note that stock `get_sd_stats()` checks `/proc/diskstats` for `mmcblk` and a partition character `'p'`, so raw `/dev/mmcblk0` without a partition needs direct `/mnt/sd` handling.

---

## Useful Commands

Configure static IP on the camera:

```sh
ip addr add 10.0.12.215/24 dev eth0
ip link set eth0 up
```

Transfer compiled binaries from `bins/` using `netcat`:

```sh
# On the camera:
nc -l -p 9010 > /mnt/mtd/bin/snap && chmod +x /mnt/mtd/bin/snap
nc -l -p 9010 > /mnt/mtd/bin/ptz_test && chmod +x /mnt/mtd/bin/ptz_test

# On the host machine:
nc -N 10.0.12.215 9010 < bins/snap
nc -N 10.0.12.215 9010 < bins/ptz_test
```

---

## Project Roadmap

### Done

* [x] Solder jumper wires to the UART port
* [x] Capture and analyze U-Boot logs
* [x] Dump SPI Flash partitions (`flash_dump/mtd0.bin`–`mtd5.bin`, `sys/mtd1_backup.bin`)
* [x] Extract `/etc/shadow` and crack the DES root password (`GM8182`) with `hashcat`
* [x] Log in via Telnet
* [x] Override `/mnt/mtd/boot.sh` (`sys/new_mnt_motd_boot.sh`) to load video/GPIO drivers, apply pinmux masks (`0x99000050`–`0x99000058`), omit `nvisr` and `cpe-wdt.ko`, and start `httpd`
* [x] Write standalone PTZ & IR control binary (`libs/ptz_test.c` -> `bins/ptz_test`) with pin direction setup (`ioctl` `2` / `6`), bank `1` pin `13`, and limit switch checks (using Ghidra)
* [x] Build `snap` (`libs/snap.c` -> `bins/snap`) to capture JPEG frames and harden `web_app/cgi-bin/snap.cgi` against existing target files and concurrent `dvr_graph` contention (`/tmp/snap.lock`)
* [x] Run a persistent BusyBox `httpd` web app (`web_app/` -> `/mnt/mtd/opt/www`) with client-synchronized snapshot updates (`index.html`, `ptz.html`, `snap.cgi`)
* [x] Make wrapper for `ptz_test` (`web_app/cgi-bin/ptz.cgi` supporting simple `pan`/`tilt`, `ircut`/`irled`, and coordinate `goto` tracking)
- [x] Configure DHCP on `eth0` and `ra0` using `/mnt/mtd/udhcpc.script` and a boot `sleep` delay for WiFi association
- [x] Get WiFi (`ra0` / RT3070) working via `iwpriv` and `udhcpc` (watching out for same-subnet routing conflicts with `eth0`)
- [x] Get MicroSD working by loading `ftsdc010.ko` and mounting `/dev/mmcblk0` at `/mnt/sd`

### Web APP

![WebApp](images/web_app.png)

### What I haven't done, but could do in the future

* [ ] Get Audio working (not necessary)
* [ ] Clean up SPI Flash (remove manufacturer bloat - not neccesary beacuse only selected .ko are loaded and you can use MicroSD)
* [ ] Get Alarm and WiFi led working (not necessary)
