#!/bin/sh

cd $(dirname $0)
./compile.sh
mkdir -p pkg
export DESTDIR=$PWD/pkg
./install.sh
VER=$(grep 'version =' src/lilosetup.py | head -n 1 | sed "s/.*'\(.*\)'/\1/")
cd pkg
cat <<EOF > install/slack-desc
lilosetup: LiloSetup - A simple GUI to setup LILO.
lilosetup: 
lilosetup: LiloSetup will enable you to create a new lilo bootloader, from the
lilosetup: comfort of a graphical interface. It can be executed both from a
lilosetup: LiveCD environment or from a standard system.
lilosetup: It supports multiboot, Windows, Linux, ata and libata subsystems,
lilosetup: 
lilosetup:
lilosetup:
lilosetup:
lilosetup:
EOF
makepkg -l y -c n ../lilosetup-$VER-noarch-1plb.txz
cd ..
echo -e "lilo,python,os-prober" > lilosetup-$VER-noarch-1plb.dep
md5sum lilosetup-$VER-noarch-1plb.txz > lilosetup-$VER-noarch-1plb.md5
rm -rf pkg
