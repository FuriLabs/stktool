PREFIX ?= /usr
LIBDIR = $(PREFIX)/lib
BINDIR = $(PREFIX)/bin
SHAREDIR = $(PREFIX)/share

INSTALL_DIR = $(LIBDIR)/stktool
DESKTOP_DIR = $(SHAREDIR)/applications
ICON_DIR = $(SHAREDIR)/icons/hicolor/scalable/apps

.PHONY: all install uninstall

all:
	@echo "Run 'make install' to install the files."

install:
	install -d $(DESTDIR)$(INSTALL_DIR)
	install -d $(DESTDIR)$(BINDIR)
	install -d $(DESTDIR)$(DESKTOP_DIR)
	install -d $(DESTDIR)$(ICON_DIR)

	cp -r stktool $(DESTDIR)$(INSTALL_DIR)/

	install -m 755 main.py $(DESTDIR)$(INSTALL_DIR)/

	install -m 644 data/io.furios.StkTool.desktop $(DESTDIR)$(DESKTOP_DIR)/
	install -m 644 data/io.furios.StkTool.svg $(DESTDIR)$(ICON_DIR)/

	ln -sf ../lib/stktool/main.py $(DESTDIR)$(BINDIR)/io.furios.StkTool

uninstall:
	rm -f $(DESTDIR)$(BINDIR)/io.furios.StkTool

	rm -rf $(DESTDIR)$(INSTALL_DIR)
	rm -f $(DESTDIR)$(DESKTOP_DIR)/io.furios.StkTool.desktop
	rm -f $(DESTDIR)$(ICON_DIR)/io.furios.StkTool.svg
