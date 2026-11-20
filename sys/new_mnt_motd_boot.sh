#!/bin/sh
chmod 777 /tmp/

/sbin/rmmod ftgpio 2>/dev/null
/sbin/insmod /lib/modules/ftgpio.ko
/sbin/insmod /lib/modules/ftmac100.ko

# Kopiowanie konfiguracji kodera DVR i matrycy
cp /product/IPC-720P/memory/gmdvr_mem.cfg /mnt/mtd/
cp /product/IPC-720P/demo/ipc.cfg /mnt/mtd/
cp /product/IPC-720P/memory/config_8126 /mnt/mtd/

# Sterowniki wideo HM1375 + enkodery H.264 / MJPEG (bez cpe-wdt.ko)
/sbin/insmod /lib/modules/frammap.ko sys_align=6 ddr0=64
/sbin/insmod /lib/modules/videograph.ko
/sbin/insmod /lib/modules/dvr_common.ko
/sbin/insmod /lib/modules/dvr_enc.ko
/sbin/insmod /lib/modules/dvr_disp.ko lcd_cnt=1 dup_disp=0
/sbin/insmod /lib/modules/flcd200-common.ko
/sbin/insmod /lib/modules/flcd200-pip.ko output_type=0 input_res=11
/sbin/insmod /lib/modules/fcap_common.ko
/sbin/insmod /lib/modules/fcap0.ko mode=1
/sbin/insmod /lib/modules/fcap1.ko mode=1
/sbin/insmod /lib/modules/fcap200_hm1375.ko inv_clk=0
/sbin/insmod /lib/modules/fscaler0.ko
/sbin/insmod /lib/modules/favc_common.ko
/sbin/insmod /lib/modules/favc_drv.ko h264_max_width=1280 h264_max_height=720
/sbin/insmod /lib/modules/fmcp_drv.ko
/sbin/insmod /lib/modules/fmjpeg_drv.ko
/sbin/insmod /lib/modules/ftdi210.ko

# Konfiguracja pinmux i zegarow SoC (z boot_hm1375.sh oraz init_gpio)
devmem 0x99300030 32 0x78
devmem 0x99300034 32 0x0e060002
devmem 0x99300038 32 0x060e0606
devmem 0x993000a0 32 0x87870187
devmem 0x993000a4 32 0x878f8787
devmem 0x98700050 32 0x00000604
devmem 0x99000058 32 0x1C502416
devmem 0x99000060 32 0xFFD75FC7
devmem 0x99700008 32 0x8000

V50=$(devmem 0x99000050)
V54=$(devmem 0x99000054)
V58=$(devmem 0x99000058)
devmem 0x99000050 32 $(( V50 & 0xfffcff00 ))
devmem 0x99000054 32 $(( V54 & 0xfffffc3f ))
devmem 0x99000058 32 $(( V58 & 0xff000003 ))

mdev -s
telnetd

ip addr add 10.0.12.215/24 dev eth0
ip link set eth0 up