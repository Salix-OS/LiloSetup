#!/bin/sh

PKGNAME=lilosetup
VER=$(grep 'version =' src/$PKGNAME.py | head -n 1 | sed "s/.*'\(.*\)'/\1/")

cd $(dirname $0)

install -d -m 755 $DESTDIR/usr/doc/$PKGNAME-$VER
install -d -m 755 $DESTDIR/usr/sbin
install -d -m 755 $DESTDIR/usr/share/applications
install -d -m 755 $DESTDIR/usr/share/icons/hicolor/24x24/apps
install -d -m 755 $DESTDIR/usr/share/icons/hicolor/64x64/apps
install -d -m 755 $DESTDIR/usr/share/icons/hicolor/128x128/apps
install -d -m 755 $DESTDIR/usr/share/icons/hicolor/scalable/apps
install -d -m 755 $DESTDIR/usr/share/$PKGNAME

install -m 755 src/$PKGNAME.py \
$DESTDIR/usr/sbin/$PKGNAME.py
install -m 644 src/$PKGNAME.glade \
$DESTDIR/usr/share/$PKGNAME
install -m 644 src/$PKGNAME.desktop \
$DESTDIR/usr/share/applications/
install -m 644 src/$PKGNAME-kde.desktop \
$DESTDIR/usr/share/applications/
install -m 644 icons/$PKGNAME-24.png \
$DESTDIR/usr/share/icons/hicolor/24x24/apps/$PKGNAME.png
install -m 644 icons/$PKGNAME-64.png \
$DESTDIR/usr/share/icons/hicolor/64x64/apps/$PKGNAME.png
install -m 644 icons/$PKGNAME-128.png \
$DESTDIR/usr/share/icons/hicolor/128x128/apps/$PKGNAME.png
install -m 644 icons/$PKGNAME.svg \
$DESTDIR/usr/share/icons/hicolor/scalable/apps/
install -m 644 src/$PKGNAME.png \
$DESTDIR/usr/share/$PKGNAME/

for i in `ls po/*.mo|sed "s|po/\(.*\).mo|\1|"`; do
	install -d -m 755 $DESTDIR/usr/share/locale/${i}/LC_MESSAGES
	install -m 644 po/${i}.mo \
	$DESTDIR/usr/share/locale/${i}/LC_MESSAGES/$PKGNAME.mo
done

for i in `ls docs`; do
	install -m 644 docs/${i} \
	$DESTDIR/usr/doc/$PKGNAME-$VER/
done
