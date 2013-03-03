#!/bin/sh

intltool-extract --type="gettext/ini" src/lilosetup.desktop.in
intltool-extract --type="gettext/ini" src/lilosetup-kde.desktop.in

xgettext --from-code=utf-8 \
	-L Glade \
	-o po/lilosetup.pot \
	src/lilosetup.glade

xgettext --from-code=utf-8 \
	-j \
	-L Python \
	-o po/lilosetup.pot \
	src/lilosetup.py

xgettext --from-code=utf-8 \
	-j \
	-L Python \
	-o po/lilosetup.pot \
	src/lilosetup_modules/liloconfigfile.py

xgettext --from-code=utf-8 -j -L C -kN_ -o po/lilosetup.pot src/lilosetup.desktop.in.h
xgettext --from-code=utf-8 -j -L C -kN_ -o po/lilosetup.pot src/lilosetup-kde.desktop.in.h

rm src/lilosetup.desktop.in.h src/lilosetup-kde.desktop.in.h

cd po
for i in `ls *.po`; do
	msgmerge -U $i lilosetup.pot
done
rm -f ./*~
