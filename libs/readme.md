
how to build ptz library:
arm-linux-gnueabi-gcc -O2 -march=armv5te -marm -mfloat-abi=soft -ffreestanding -fno-builtin -nostdlib -static ptz_test.c -o ptz_test

how to build snap library:
arm-linux-gnueabi-gcc -O2 -march=armv5te -marm -mfloat-abi=soft -ffreestanding -fno-builtin -nostdlib -static ~/tmp/snap.c -o ~/tmp/snap && arm-linux-gnueabi-strip ~/tmp/snap