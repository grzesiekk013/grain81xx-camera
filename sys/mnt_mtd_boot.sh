chmod 777 /tmp/
mkdir /mnt/mtd/update
mkdir /mnt/mtd/update/file

cp /mnt/mtd/update/file/*so* /lib/
cp /mnt/mtd/update/file/*ko /lib/modules/
cp /mnt/mtd/update/file/nvisr /bin/
cp /mnt/mtd/update/file/boot.sh /mnt/mtd/boot.sh


/sbin/rmmod ftgpio
/sbin/insmod /lib/modules/ftgpio.ko

#echo 3 >/sys/class/gpio/export
#echo out >/sys/class/gpio/gpio3/direction
#echo 0 >/sys/class/gpio/gpio3/value
#usleep 200000
#echo 1 >/sys/class/gpio/gpio3/value

/sbin/insmod /lib/modules/ftmac100.ko
/sbin/insmod /lib/modules/cpe-wdt.ko

/sbin/insmod /lib/modules/rtc-pcf8563.ko
/sbin/insmod /lib/modules/pcf8563_dev.ko
mdev -s

#ifconfig eth0 192.168.3.180
telnetd
#rm /lib/modules/ -rf
sleep 3
nvisr
