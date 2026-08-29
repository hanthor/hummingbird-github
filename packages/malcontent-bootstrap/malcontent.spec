# Bootstrap build of malcontent: libmalcontent only, no UI.
#
# malcontent BuildRequires pkgconfig(flatpak), and flatpak-libs requires
# libmalcontent-0.so.0. In Fedora that resolves because Fedora's own
# malcontent-libs installs; here it cannot, because it requires
# libaccountsservice.so.0 and our accountsservice 26.27.3 provides .so.1. So
# malcontent transitively BuildRequires itself, and neither it nor
# gnome-control-center could resolve a buildroot:
#
#   package flatpak-libs-1.18.1-1.fc44.x86_64 from updates requires
#     libmalcontent-0.so.0()(64bit), but none of the providers can be installed
#   package malcontent-libs-0.14.0-1.fc44.x86_64 from fedora requires
#     libaccountsservice.so.0()(64bit), but none of the providers can be installed
#
# flatpak is reached only through libmalcontent-ui, which meson enters solely
# under `if get_option('ui').enabled()` -- upstream separates it deliberately,
# and ships a use_system_libmalcontent option described as "used in distros to
# break a dependency cycle". So this pass builds with -Dui=disabled, which needs
# no flatpak, and produces a malcontent-libs linked against accountsservice 26.
# The full build one stage later resolves against it.
#
# Release is 0.bootstrap so it sorts BELOW the real 1.hum1.bfin build: at the next
# stage this is the only malcontent in [stages] and so gets used, and anywhere
# both exist the full one wins on version. publish deletes it rather than
# shipping a malcontent with no parental controls UI.
#
# This is a copy of ../malcontent/malcontent.spec with the UI removed. Both are
# built in the same run, so a change made to one and not to this shows up as a
# build failure rather than as silent drift.

Name:           malcontent
Version:        0.14.0
Release:        0.bootstrap%{?dist}
Summary:        Parental controls implementation

License:        LGPL-2.1-only AND CC-BY-3.0
URL:            https://gitlab.freedesktop.org/pwithnall/%{name}/
Source0:        https://tecnocode.co.uk/downloads/%{name}/%{name}-%{gnome_tarball_version}.tar.xz
Source1:        https://gitlab.gnome.org/pwithnall/libgsystemservice/-/archive/0.3.0/libgsystemservice-0.3.0.tar.bz2
Source2:        gvdb.tar.xz
Source3:        http://www.corpit.ru/mjt/tinycdb/tinycdb-0.81.tar.gz

%gnome_check_version

BuildRequires:  gettext
BuildRequires:  gi-docgen
BuildRequires:  meson
BuildRequires:  cmake
BuildRequires:  git-core
BuildRequires:  gcc
BuildRequires:  itstool
BuildRequires:  pkgconfig(gobject-introspection-1.0)
BuildRequires:  pkgconfig(dbus-1)
BuildRequires:  pkgconfig(polkit-gobject-1)
BuildRequires:  pkgconfig(accountsservice)
BuildRequires:  pkgconfig(glib-testing-0)
BuildRequires:  pam-devel
BuildRequires:  gtk-doc
BuildRequires:  libsoup3-devel

Provides:       bundled(gvdb)
Provides:       bundled(libgsystemservice)
Provides:       bundled(tinycdb)

Requires: polkit

# Descriptions mostly gathered from:
# https://github.com/endlessm/malcontent/blob/debian-master/debian/control

%description
libmalcontent implements parental controls support which can be used by
applications to filter or limit the access of child accounts to inappropriate
content.

%package pam
Summary:        Parental Controls PAM Module

%description pam
This package contains a PAM module which prevents logins for users who have
exceeded their allowed computer time.

%package tools
Summary:        Parental Controls Tools
Requires:       %{name}%{?_isa} = %{version}-%{release}

%description tools
This package contains tools for querying and updating the parental controls
settings for users.

%package devel
Summary:        Development files for %{name}
Requires:       %{name}-libs%{?_isa} = %{version}-%{release}

%description devel
This package contains the pkg-config file and development headers
for %{name}.

%package libs
Summary:        Libraries for %{name}

%description libs
This package contains libmalcontent.

%package doc
Summary:        Documentation for %{name}

%description doc
This package documentation for libmalcontent.


%prep
%autosetup -p1 -n %{name}-%{gnome_tarball_version} -S git
tar -xf %{SOURCE1} -C subprojects
mv subprojects/libgsystemservice-0.3.0 subprojects/libgsystemservice
tar -xf %{SOURCE2} -C subprojects
tar -xf %{SOURCE3} -C subprojects
cp subprojects/packagefiles/tinycdb/meson.build subprojects/tinycdb-0.81

%build
%meson -Dui=disabled -Dinstalled_tests=false
%meson_build

%install
%meson_install
%find_lang %{name} --with-gnome

%files -f %{name}.lang
%license COPYING COPYING-DOCS
%doc README.md
%{_datadir}/accountsservice/interfaces/
%{_datadir}/dbus-1/interfaces/
%{_datadir}/polkit-1/actions/*.policy
%{_datadir}/polkit-1/rules.d/com.endlessm.ParentalControls.rules
%{_libexecdir}/malcontent-timer-extension-agent
%{_libexecdir}/malcontent-timerd
%{_libexecdir}/malcontent-webd
%{_libexecdir}/malcontent-webd-update
%{_datadir}/dbus-1/system-services/org.freedesktop.MalcontentTimer1.ExtensionAgent.service
%{_datadir}/dbus-1/system-services/org.freedesktop.MalcontentTimer1.service
%{_datadir}/dbus-1/system-services/org.freedesktop.MalcontentWeb1.service
%{_datadir}/dbus-1/system.d/org.freedesktop.MalcontentTimer1.ExtensionAgent.conf
%{_datadir}/dbus-1/system.d/org.freedesktop.MalcontentTimer1.conf
%{_datadir}/dbus-1/system.d/org.freedesktop.MalcontentWeb1.conf
%{_mandir}/man8/malcontent-timer-extension-agent.8*
%{_mandir}/man8/malcontent-timerd.8*
%{_mandir}/man8/malcontent-webd.8*
%{_unitdir}/malcontent-timer-extension-agent.service
%{_unitdir}/malcontent-timerd.service
%{_unitdir}/malcontent-webd-update.service
%{_unitdir}/malcontent-webd-update.timer
%{_unitdir}/malcontent-webd.service
%{_sysusersdir}/malcontent-timer-extension-agent.conf
%{_sysusersdir}/malcontent-timerd.conf
%{_sysusersdir}/malcontent-webd.conf
%exclude %{_libexecdir}/installed-tests/malcontent-webd-update-1/malcontent-webd-template.py


%files pam
%license COPYING
%{_libdir}/security/pam_malcontent.so

%files tools
%license COPYING
%{_bindir}/malcontent-client
%{_mandir}/man8/malcontent-client.8.*

%files devel
%dir %{_datadir}/gir-1.0
%{_datadir}/gir-1.0/Malcontent-0.gir
%{_includedir}/malcontent-0/
%{_libdir}/libmalcontent-0.so
%{_libdir}/pkgconfig/malcontent-0.pc

%files libs
%license COPYING
%doc README.md
%dir %{_libdir}/girepository-1.0/
%{_libdir}/girepository-1.0/Malcontent-0.typelib
%{_libdir}/libmalcontent-0.so.*
%{_libdir}/libnss_malcontent.so*

%files doc
%{_docdir}/libmalcontent-0


%changelog
%autochangelog
