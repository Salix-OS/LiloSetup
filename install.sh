#!/bin/sh

VER=$(grep 'version =' src/lilosetup.py | head -n 1 | sed "s/.*'\(.*\)'/\1/")

cd $(dirname $0)
install -d -m 755 $DESTDIR/usr/doc/lilosetup-$VER
install -d -m 755 $DESTDIR/install
install -d -m 755 $DESTDIR/usr/sbin
install -d -m 755 $DESTDIR/usr/share/applications
install -d -m 755 $DESTDIR/usr/share/icons/hicolor/24x24/apps
install -d -m 755 $DESTDIR/usr/share/icons/hicolor/64x64/apps
install -d -m 755 $DESTDIR/usr/share/icons/hicolor/128x128/apps
install -d -m 755 $DESTDIR/usr/share/icons/hicolor/scalable/apps
install -d -m 755 $DESTDIR/usr/share/lilosetup

install -m 755 src/lilosetup.py $DESTDIR/usr/sbin/lilosetup.py
install -m 644 src/lilosetup.glade \
$DESTDIR/usr/share/lilosetup
install -m 644 src/lilosetup.desktop \
$DESTDIR/usr/share/applications/
install -m 644 icons/lilosetup-24.png \
$DESTDIR/usr/share/icons/hicolor/24x24/apps/lilosetup.png
install -m 644 icons/lilosetup-64.png \
$DESTDIR/usr/share/icons/hicolor/64x64/apps/lilosetup.png
install -m 644 icons/lilosetup-128.png \
$DESTDIR/usr/share/icons/hicolor/128x128/apps/lilosetup.png
install -m 644 icons/lilosetup.svg \
$DESTDIR/usr/share/icons/hicolor/scalable/apps/
install -m 644 src/lilosetup.png \
$DESTDIR/usr/share/lilosetup/

for i in `ls po/*.mo|sed "s|po/\(.*\).mo|\1|"`; do
	install -d -m 755 $DESTDIR/usr/share/locale/${i}/LC_MESSAGES
	install -m 644 po/${i}.mo \
	$DESTDIR/usr/share/locale/${i}/LC_MESSAGES/lilosetup.mo
done

for i in `ls docs`; do
	install -m 644 docs/${i} \
	$DESTDIR/usr/doc/lilosetup-$VER/
done
