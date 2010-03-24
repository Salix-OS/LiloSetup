#!/bin/sh

intltool-extract --type="gettext/ini" src/lilosetup.desktop.in

xgettext --from-code=utf-8 \
	-L Glade \
	-o po/lilosetup.pot \
	src/lilosetup.glade

xgettext --from-code=utf-8 \
	-j \
	-L Python \
	-o po/lilosetup.pot \
	src/lilosetup.py
xgettext --from-code=utf-8 -j -L C -kN_ -o po/lilosetup.pot src/lilosetup.desktop.in.h

rm src/lilosetup.desktop.in.h

cd po
for i in `ls *.po`; do
	msgmerge -U $i lilosetup.pot
done
rm -f ./*~

