# Makefile for sys_knobs kernel module
# Uses the kbuild mechanism (same approach as the reading material)
#
# Usage:
#   make          – build the .ko kernel object
#   make clean    – remove build artefacts

obj-m = sys_knobs.o

all:
	make -C /lib/modules/$(shell uname -r)/build M=$(PWD) modules

clean:
	make -C /lib/modules/$(shell uname -r)/build M=$(PWD) clean
