
how to build ptz library:
arm-linux-gnueabi-gcc -O2 -march=armv5te -marm -mfloat-abi=soft -ffreestanding -fno-builtin -nostdlib -static ptz_test.c -o ptz_test

how to build snap library:
arm-linux-gnueabi-gcc -O2 -march=armv5te -marm -mfloat-abi=soft -ffreestanding -fno-builtin -nostdlib -static ~/tmp/snap.c -o ~/tmp/snap && arm-linux-gnueabi-strip ~/tmp/snap

how to build snap hook lib:
arm-linux-gnueabi-gcc -shared -fPIC -O2 -march=armv5te -marm -mfloat-abi=soft -fno-stack-protector -U_FORTIFY_SOURCE ~/tmp/snap_hook.c -o ~/tmp/libsnaphook.so
arm-linux-gnueabi-strip ~/tmp/libsnaphook.so

check if glibc...
 arm-linux-gnueabi-readelf -s -W ~/tmp/libsnaphook.so | grep '@GLIBC_2.34' || echo "Brak GLIBC_2.34"