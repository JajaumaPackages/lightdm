
# FIXME: most tests currently fail
#define tests 1

Name:    lightdm
Summary: A cross-desktop Display Manager
Version: 1.19.5
Release: 1%{?dist}

# library/bindings are LGPLv2 or LGPLv3, the rest GPLv3+
License: (LGPLv2 or LGPLv3) and GPLv3+
URL:     https://launchpad.net/lightdm/1.19
Source0: https://launchpad.net/lightdm/1.19/%{version}/+download/lightdm-%{version}.tar.xz

Source1: lightdm.pam
Source2: lightdm-autologin.pam
Source3: lightdm-tmpfiles.conf
Source4: lightdm.service
Source5: lightdm.logrotate
Source6: lightdm.rules

## .conf snippets
# use logrotate?
Source10: 50-backup-logs.conf
Source11: 50-minimum-vt.conf
Source12: 50-session-wrapper.conf
Source13: 50-user-authority-in-system-dir.conf
Source14: 50-xserver-command.conf

## Downstream patches:
# hack in support for --nodaemon option
Patch11: lightdm-1.10.2-nodaemon_option.patch
# disable saving to ~/.dmrc (runs afoul of selinux, http://bugzilla.redhat.com/963238 )
Patch12: lightdm-1.9.8-no_dmrc_save.patch

## upstreamable patches
# search for moc-qt5, use -qt=5|4 (instead of --qt=qt4|qt5)
Patch51:  lightdm-1.18-qtchooser.patch

# patch51
BuildRequires: gettext
BuildRequires: gnome-common
BuildRequires: gtk-doc itstool
BuildRequires: intltool
BuildRequires: libgcrypt-devel
BuildRequires: pam-devel
BuildRequires: pkgconfig(audit)
BuildRequires: pkgconfig(dbus-glib-1)
BuildRequires: pkgconfig(gio-2.0) >= 2.26
BuildRequires: pkgconfig(gio-unix-2.0)
BuildRequires: pkgconfig(glib-2.0)
BuildRequires: pkgconfig(gmodule-export-2.0)
BuildRequires: pkgconfig(gobject-2.0)
%global glib2_version %(pkg-config --modversion glib-2.0 2>/dev/null || echo "2.10")
BuildRequires: pkgconfig(gobject-introspection-1.0) >= 0.9.5
BuildRequires: pkgconfig(libxklavier)
BuildRequires: pkgconfig(QtCore) pkgconfig(QtDBus) pkgconfig(QtGui) pkgconfig(QtNetwork)
BuildRequires: pkgconfig(x11)
BuildRequires: pkgconfig(xcb)
BuildRequires: pkgconfig(xdmcp)
BuildRequires: systemd
BuildRequires: vala vala-tools

Requires: %{name}-gobject%{?_isa} = %{version}-%{release}
Requires: accountsservice
Requires: dbus-x11
%if 0%{?rhel} > 6 || 0%{?fedora} > 18
Requires: polkit-js-engine
%endif
Requires: systemd
%{?systemd_requires}
Requires: xorg-x11-xinit

Requires(pre): shadow-utils

# beware of bootstrapping -- rex
# leaving this here, means greeters will have to require lightdm too,
# instead of relying on -gobject, -qt to pull it in
Requires: lightdm-greeter = 1.2

# needed for anaconda to boot into runlevel 5 after install
Provides: service(graphical-login) = lightdm

%description
Lightdm is a display manager that:
* Is cross-desktop - supports different desktops
* Supports different display technologies
* Is lightweight - low memory usage and fast performance

%package gobject
Summary: LightDM GObject client library
# omit base package, to allow for easier bootstrapping
# requires greeters to manually
# Requires: lightdm
#Requires: %{name} = %{version}-%{release}
Requires: glib2%{?_isa} >= %{glib2_version}
%description gobject
This package contains a GObject based library for LightDM clients to use to
interface with LightDM.

%package gobject-devel
Summary: Development files for %{name}-gobject
Requires: %{name}-gobject%{?_isa} = %{version}-%{release}
%description gobject-devel
%{summary}.

%package qt
Summary: LightDM Qt4 client library
# see comment in -gobject above
#Requires: %{name} = %{version}-%{release}
%{?_qt4_version:Requires: qt4%{?_isa} >= %{_qt4_version}}
%description qt
This package contains a Qt4-based library for LightDM clients to use to interface
with LightDM.

%package qt-devel
Summary: Development files for %{name}-qt
Requires: %{name}-qt%{?_isa} = %{version}-%{release}
%description qt-devel
%{summary}.


%prep
%setup -q

%patch11 -p1 -b .nodaemon_option
%patch12 -p1 -b .no_dmrc_save

%patch51 -p1 -b .qtchooser

# rpath hack
sed -i -e 's|"/lib /usr/lib|"/%{_lib} %{_libdir}|' configure


%build
%configure \
  --disable-static \
  --enable-gtk-doc \
  --enable-libaudit \
  --enable-liblightdm-qt \
  --enable-introspection \
  %{?tests:--enable-tests}%{!?tests:--disable-tests} \
  --enable-vala \
  --with-greeter-user=lightdm \
  --with-greeter-session=lightdm-greeter

make %{?_smp_mflags} V=1


%install
make install DESTDIR=%{buildroot} INSTALL='install -p'

## unpackaged files
# libtool cruft
rm -fv %{buildroot}%{_libdir}/lib*.la
# We don't ship AppAmor
rm -rfv %{buildroot}%{_sysconfdir}/apparmor.d/
# omit upstart support
rm -rfv %{buildroot}%{_sysconfdir}/init

# install pam file
install -Dpm 644 %{SOURCE1} %{buildroot}%{_sysconfdir}/pam.d/lightdm
install -Dpm 644 %{SOURCE2} %{buildroot}%{_sysconfdir}/pam.d/lightdm-autologin

install -Dpm 644 %{SOURCE3} %{buildroot}%{_prefix}/lib/tmpfiles.d/lightdm.conf

# We need to own these
mkdir -p %{buildroot}%{_sysconfdir}/lightdm/lightdm.conf.d/
mkdir -p %{buildroot}%{_datadir}/lightdm/lightdm.conf.d/
mkdir -p %{buildroot}%{_datadir}/lightdm/remote-sessions/
mkdir -p %{buildroot}%{_localstatedir}/cache/lightdm/
mkdir -p %{buildroot}%{_localstatedir}/run/lightdm/
mkdir -p %{buildroot}%{_localstatedir}/log/lightdm/
mkdir -p %{buildroot}%{_localstatedir}/lib/lightdm/
mkdir -p %{buildroot}%{_localstatedir}/lib/lightdm-data/

%find_lang %{name} --with-gnome

install -m644 -p -D %{SOURCE4} %{buildroot}%{_unitdir}/lightdm.service
install -m644 -p -D %{SOURCE5} %{buildroot}%{_sysconfdir}/logrotate.d/lightdm
install -m644 -p -D %{SOURCE6} %{buildroot}%{_datadir}/polkit-1/rules.d/lightdm.rules
install -m644 -p %{SOURCE10} %{SOURCE11} %{SOURCE12} %{SOURCE13} %{SOURCE14} \
  %{buildroot}%{_datadir}/lightdm/lightdm.conf.d/

%check
# FIXME: most of these currently fail :( -- rex
%if 0%{?tests:1}
make check ||:
%endif


%pre
getent group lightdm >/dev/null || groupadd -r lightdm
getent passwd lightdm >/dev/null || \
  /usr/sbin/useradd -g lightdm -M -d /var/lib/lightdm -s /sbin/nologin -r lightdm
exit 0

%post
%{?systemd_post:%systemd_post lightdm.service}

%preun
%{?systemd_preun:%systemd_preun lightdm.service}

%postun
%{?systemd_postun}

%files -f %{name}.lang
%license COPYING.GPL3
%doc NEWS
%config(noreplace) %{_sysconfdir}/dbus-1/system.d/org.freedesktop.DisplayManager.conf
%config(noreplace) %{_sysconfdir}/pam.d/lightdm*
%dir %{_sysconfdir}/lightdm/
%dir %{_sysconfdir}/lightdm/lightdm.conf.d
%config(noreplace) %{_sysconfdir}/lightdm/keys.conf
%config(noreplace) %{_sysconfdir}/lightdm/lightdm.conf
%config(noreplace) %{_sysconfdir}/lightdm/users.conf
%dir %{_sysconfdir}/logrotate.d/
%{_sysconfdir}/logrotate.d/lightdm
%{_bindir}/dm-tool
%{_sbindir}/lightdm
%{_libexecdir}/lightdm-guest-session
%{_datadir}/lightdm/
%{_libdir}/girepository-1.0/LightDM-1.typelib
%{_mandir}/man1/dm-tool.1*
%{_mandir}/man1/lightdm*
%dir %attr(-,lightdm,lightdm) %{_localstatedir}/cache/lightdm/
%{_unitdir}/lightdm.service
%{_datadir}/polkit-1/rules.d/lightdm.rules
%dir %{_datadir}/bash-completion/
%dir %{_datadir}/bash-completion/completions/
%{_datadir}/bash-completion/completions/dm-tool
%{_datadir}/bash-completion/completions/lightdm

# because of systemd
%{_prefix}/lib/tmpfiles.d/lightdm.conf
%ghost %dir %{_localstatedir}/run/lightdm

%dir %attr(-,lightdm,lightdm) %{_localstatedir}/lib/lightdm/
%dir %attr(-,lightdm,lightdm) %{_localstatedir}/lib/lightdm-data/
%dir %attr(-,lightdm,lightdm) %{_localstatedir}/log/lightdm/

%post gobject -p /sbin/ldconfig
%postun gobject -p /sbin/ldconfig

%files gobject
%license COPYING.LGPL2 COPYING.LGPL3
%{_libdir}/liblightdm-gobject-1.so.0*

%files gobject-devel
%doc %{_datadir}/gtk-doc/html/lightdm-gobject-1/
%{_includedir}/lightdm-gobject-1/
%{_libdir}/liblightdm-gobject-1.so
%{_libdir}/pkgconfig/liblightdm-gobject-1.pc
%{_datadir}/gir-1.0/LightDM-1.gir
%{_datadir}/vala/vapi/liblightdm-gobject-1.*

%post qt -p /sbin/ldconfig
%postun qt -p /sbin/ldconfig

%files qt
%license COPYING.LGPL2 COPYING.LGPL3
%{_libdir}/liblightdm-qt-3.so.0*

%files qt-devel
%{_includedir}/lightdm-qt-3/
%{_libdir}/liblightdm-qt-3.so
%{_libdir}/pkgconfig/liblightdm-qt-3.pc


%changelog
* Fri Sep 30 2016 Jajauma's Packages <jajauma@yandex.ru> - 1.19.5-1
- Update to latest upstream release
- Drop Qt5 subpackage for RHEL

* Thu Jul 07 2016 Rex Dieter <rdieter@fedoraproject.org> 1.18.2-1
- lightdm-1.18.2

* Mon Apr 04 2016 Rex Dieter <rdieter@fedoraproject.org> - 1.18.1-1
- lightdm-1.18.1

* Sat Apr 02 2016 Rex Dieter <rdieter@fedoraproject.org> - 1.18.0-1
- lightdm-1.18.0 (#1321032)
- use lightdm.conf.d/ snippets for default configuration (instead of patching) (#1096216)

* Thu Feb 04 2016 Fedora Release Engineering <releng@fedoraproject.org> - 1.10.6-3
- Rebuilt for https://fedoraproject.org/wiki/Fedora_24_Mass_Rebuild

* Wed Nov 25 2015 Rex Dieter <rdieter@fedoraproject.org> - 1.10.6-2
- enable libaudit support
- (re)enable hardening for f23+, at least (#956868)
- disable tests
- drop now-unused lightdm.pam.f19

* Fri Nov 20 2015 Rex Dieter <rdieter@fedoraproject.org> 1.10.6-1
- 1.10.6

* Mon Oct 12 2015 Rex Dieter <rdieter@fedoraproject.org> 1.10.5-7
- use upstream listen.patch instead

* Tue Oct 06 2015 Rex Dieter <rdieter@fedoraproject.org> 1.10.5-6
- drop listen.patch for < f22 (#1269247)

* Thu Sep 24 2015 Rex Dieter <rdieter@fedoraproject.org> 1.10.5-5
- update Summary/%%description

* Thu Sep 10 2015 Rex Dieter <rdieter@fedoraproject.org> 1.10.5-4
- lightdm.pam: add pam_kwallet5 support

* Tue Sep 08 2015 Rex Dieter <rdieter@fedoraproject.org> 1.10.5-3
- rework -qtchooser.patch to avoid autoreconf'ing (fixes epel7 build)

* Fri Aug 28 2015 Rex Dieter <rdieter@fedoraproject.org> 1.10.5-2
- Lightdm runs without -nolisten but X not listening (#12255743)

* Mon Aug 17 2015 Rex Dieter <rdieter@fedoraproject.org> 1.10.5-1
- 1.10.5, add liblightdm-qt5 support

* Wed Jun 17 2015 Fedora Release Engineering <rel-eng@lists.fedoraproject.org> - 1.10.4-8
- Rebuilt for https://fedoraproject.org/wiki/Fedora_23_Mass_Rebuild

* Sat May 02 2015 Kalev Lember <kalevlember@gmail.com> - 1.10.4-7
- Rebuilt for GCC 5 C++11 ABI change

* Wed Apr 15 2015 Rex Dieter <rdieter@fedoraproject.org> 1.10.4-6
- -gobject: add versioned Requires: glib2 dep

* Tue Feb 24 2015 Rex Dieter <rdieter@fedoraproject.org> 1.10.4-5
- try harder to disable hardening

* Sun Feb 22 2015 Rex Dieter <rdieter@fedoraproject.org> 1.10.4-3
- explicitly disable hardening (#956868)

* Sat Feb 21 2015 Till Maas <opensource@till.name> - 1.10.4-2
- Rebuilt for Fedora 23 Change
  https://fedoraproject.org/wiki/Changes/Harden_all_packages_with_position-independent_code

* Thu Nov 13 2014 Rex Dieter <rdieter@fedoraproject.org> 1.10.4-1
- lightdm-1.10.4, update URL to 1.10-specific branch

* Thu Oct 09 2014 Rex Dieter <rdieter@fedoraproject.org> 1.10.3-1
- lightdm-1.10.3

* Mon Oct 06 2014 Rex Dieter <rdieter@fedoraproject.org> 1.10.2-2
- respin/fix fedora_config.patch (properly use [SeatDefaults] section)

* Wed Sep 17 2014 Rex Dieter <rdieter@fedoraproject.org> 1.10.2-1
- lightdm-1.10.2

* Sun Aug 17 2014 Fedora Release Engineering <rel-eng@lists.fedoraproject.org> - 1.10.1-5
- Rebuilt for https://fedoraproject.org/wiki/Fedora_21_22_Mass_Rebuild

* Tue Jul 22 2014 Kalev Lember <kalevlember@gmail.com> - 1.10.1-4
- Rebuilt for gobject-introspection 1.41.4

* Sat Jun 07 2014 Fedora Release Engineering <rel-eng@lists.fedoraproject.org> - 1.10.1-3
- Rebuilt for https://fedoraproject.org/wiki/Fedora_21_Mass_Rebuild

* Thu May 01 2014 Rex Dieter <rdieter@fedoraproject.org> 1.10.1-2
- update pam config (+pam-kwallet,-mate-keying-pam)

* Sun Apr 27 2014 Rex Dieter <rdieter@fedoraproject.org> 1.10.1-1
- lightdm-1.10.1

* Thu Apr 17 2014 Rex Dieter <rdieter@fedoraproject.org> 1.10.0-1
- lightdm-1.10.0 (#1077562)

* Thu Mar 27 2014 Rex Dieter <rdieter@fedoraproject.org> 1.9.13-2
- Could not create user data directory /var/lib/lightdm-data/lightdm (#1081426)

* Tue Mar 25 2014 Rex Dieter <rdieter@fedoraproject.org> 1.9.13-1
- lightdm-1.9.13

* Thu Mar 13 2014 Rex Dieter <rdieter@fedoraproject.org> 1.9.11-1
- lightdm-1.9.11

* Tue Mar 11 2014 Rex Dieter <rdieter@fedoraproject.org> 1.9.9-1
- lightdm-1.9.9

* Thu Feb 20 2014 Rex Dieter <rdieter@fedoraproject.org> 1.9.8-1
- lightdm-1.9.8 (#1021834)
- lightdm adds /usr/libexec/lightdm: to user $PATH (#888337)

* Thu Feb 06 2014 Rex Dieter <rdieter@fedoraproject.org> 1.8.7-1
- lightdm-1.8.7

* Wed Jan 22 2014 Rex Dieter <rdieter@fedoraproject.org> 1.8.6-1
- lightdm-1.8.6

* Fri Nov 15 2013 Rex Dieter <rdieter@fedoraproject.org> 1.8.5-2
- create/own lightdm.conf.d dirs

* Fri Nov 08 2013 Rex Dieter <rdieter@fedoraproject.org> 1.8.5-1
- lightdm-1.8.5

* Fri Nov 01 2013 Rex Dieter <rdieter@fedoraproject.org> 1.8.4-1
- lightdm-1.8.4

* Wed Oct 30 2013 Rex Dieter <rdieter@fedoraproject.org> 1.8.3-1
- lightdm-1.8.3

* Wed Oct 16 2013 Rex Dieter <rdieter@fedoraproject.org> 1.8.2-1
- lightdm-1.8.2

* Thu Oct 10 2013 Rex Dieter <rdieter@fedoraproject.org> 1.8.1-1
- lightdm-1.8.1

* Wed Oct 09 2013 Rex Dieter <rdieter@fedoraproject.org> 1.8.0-2
- lightdm has no service file (#1017390)

* Wed Oct 09 2013 Rex Dieter <rdieter@fedoraproject.org> 1.8.0-1
- lightdm-1.8.0 (#1017081)

* Tue Oct 08 2013 Rex Dieter <rdieter@fedoraproject.org> 1.7.18-2
- systemd support no longer conditional/optional
- lightdm user home /var/lib/lightdm (instead of /var/log/lightdm)

* Mon Oct 07 2013 Rex Dieter <rdieter@fedoraproject.org> 1.7.18-1
- lightdm-1.7.18 (#1016230)

* Sat Oct 05 2013 Rex Dieter <rdieter@fedoraproject.org> 1.7.17-2
- lightdm does not maintain login history using /var/log/wtmp (#1014285)
- Lightdm leaks 6 FDs (#973584)

* Tue Sep 24 2013 Rex Dieter <rdieter@fedoraproject.org> 1.7.17-1
- lightdm-1.7.17

* Sat Sep 21 2013 Rex Dieter <rdieter@fedoraproject.org> - 1.7.16-1
- lightdm-1.7.16 (#1010183)
- add %%check (mostly useless now, but wip)
- cleanup scriptlets

* Thu Sep 12 2013 Rex Dieter <rdieter@fedoraproject.org> - 1.7.15-1
- 1.7.15 (#1006773)
- Word-readable .Xauthority (#1007187, CVE-2013-4331)

* Mon Sep 09 2013 Rex Dieter <rdieter@fedoraproject.org> 1.7.13-1
- 1.7.13

* Fri Sep 06 2013 Rex Dieter <rdieter@fedoraproject.org> 1.7.12-1
- 1.7.12 (#1001101)

* Tue Aug 27 2013 Rex Dieter <rdieter@fedoraproject.org> 1.7.11-2
- rebase nodaemon_option.patch

* Mon Aug 26 2013 Dan Mashal <dan.mashal@fedoraproject.org> - 1.7.11-1
- Update to 1.7.11

* Tue Aug 20 2013 Rex Dieter <rdieter@fedoraproject.org> 1.7.9-3
- remove systemd preset (#963899)

* Thu Aug 08 2013 Rex Dieter <rdieter@fedoraproject.org> 1.7.9-2
- rebase patches (thanks poma)

* Sat Aug 03 2013 Rex Dieter <rdieter@fedoraproject.org> 1.7.9-1
- lightdm-1.7.9 (#975998)

* Sat Aug 03 2013 Fedora Release Engineering <rel-eng@lists.fedoraproject.org> - 1.6.0-11
- Rebuilt for https://fedoraproject.org/wiki/Fedora_20_Mass_Rebuild

* Thu Jun 20 2013 Rex Dieter <rdieter@fedoraproject.org> 1.6.0-10
- fix systemd-logind support in -gobject bindings (#973618)

* Thu May 23 2013 Rex Dieter <rdieter@fedoraproject.org> 1.6.0-9
- really apply no_dmrc_save.patch (#963238)

* Tue May 21 2013 Rex Dieter <rdieter@fedoraproject.org> 1.6.0-8
- revert "lightdm is misusing the preset file logic of systemd" (#963899)

* Tue May 21 2013 Rex Dieter <rdieter@fedoraproject.org> 1.6.0-7
- cleanup/fix use of systemd macros

* Mon May 20 2013 Rex Dieter <rdieter@fedoraproject.org> 1.6.0-6
- disable lightdm writing to ~/.dmrc (#963238), 
  workaround selinux policy issue, use accountsservice exclusively.
- lightdm is misusing the preset file logic of systemd (#963899)

* Thu May 16 2013 Rex Dieter <rdieter@fedoraproject.org> 1.6.0-5
- %%post: setsebool -P xdm_write_home on (#963238)

* Thu Apr 25 2013 Rex Dieter <rdieter@fedoraproject.org> 1.6.0-4
- revert building PIE to avoid crashes (#956868)

* Thu Apr 25 2013 Rex Dieter <rdieter@fedoraproject.org> 1.6.0-3
- lightdm package should be built with PIE flags (#955147)
- apply systemd patch unconditionally

* Sun Apr 14 2013 Rex Dieter <rdieter@fedoraproject.org> 1.6.0-2
- lightdm does not honor UID_MIN from /etc/login.defs (#907312)

* Sun Apr 14 2013 Rex Dieter <rdieter@fedoraproject.org> 1.6.0-1
- lightdm-1.6.0
- No login key is writen in Mate-Desktop (#896130)

* Tue Apr 02 2013 Rex Dieter <rdieter@fedoraproject.org> 1.5.3-1
- lightdm-1.5.3

* Wed Mar 27 2013 Rex Dieter <rdieter@fedoraproject.org> 1.5.2-2
- lightdm.conf: +xserver-command=X -background none

* Wed Mar 27 2013 Rex Dieter <rdieter@fedoraproject.org> 1.5.2-1
- lightdm-1.5.2 (#928255)

* Sat Mar 09 2013 Rex Dieter <rdieter@fedoraproject.org> 1.5.1-1
- lightdm-1.5.1 (#919543)

* Fri Feb 22 2013 Rex Dieter <rdieter@fedoraproject.org> 1.5.0-3
- drop Requires: ConsoleKit (f18+)

* Wed Feb 06 2013 Rex Dieter <rdieter@fedoraproject.org> 1.5.0-2
- own %%_datadir/lightdm{,/remote-sessions}
- fix/cleanup macro usage

* Thu Jan 31 2013 Rex Dieter <rdieter@fedoraproject.org> 1.5.0-1
- lightdm-1.5.0
- License: (LGPLv2 or LGPLv3) and GPLv3+

* Thu Jan 31 2013 Rex Dieter <rdieter@fedoraproject.org> 1.4.0-6
- Requires: polkit-js-engine (f19+)

* Thu Jan 10 2013 Rex Dieter <rdieter@fedoraproject.org> 1.4.0-5
- polish systemd-login1 power support patch

* Tue Jan 08 2013 Rex Dieter <rdieter@fedoraproject.org> 1.4.0-4
- omit upstart/init support from packaging (#892157)

* Mon Nov 05 2012 Rex Dieter <rdieter@fedoraproject.org> 1.4.0-3
- native org.freedesktop.login1.(PowerOff|Reboot) support (#872797)

* Mon Nov 05 2012 Rex Dieter <rdieter@fedoraproject.org> 1.4.0-2
- lightdm: provide polkit .rules for actions (#872797)

* Fri Oct 05 2012 Gregor Tätzner <brummbq@fedoraproject.org> - 1.4.0-1
- lightdm-1.4.0

* Tue Sep 04 2012 Rex Dieter <rdieter@fedoraproject.org> 1.3.3-2
- lightdm.service: After=+livesys-late.service (#853985)

* Thu Aug 30 2012 Rex Dieter <rdieter@fedoraproject.org> - 1.3.3-1
- lightdm-1.3.3
- ship systemd preset for lightdm (#852845)

* Fri Aug 10 2012 Rex Dieter <rdieter@fedoraproject.org> - 1.3.2-7
- conditionalize systemd unit support
- lightdm.pam: +-session optional pam_ck_connector.so

* Tue Aug  7 2012 Lennart Poettering <lpoetter@redhat.com> - 1.3.2-6
- Add bus name to service file

* Tue Aug  7 2012 Lennart Poettering <lpoetter@redhat.com> - 1.3.2-5
- Display Manager Rework
- https://fedoraproject.org/wiki/Features/DisplayManagerRework
- https://bugzilla.redhat.com/show_bug.cgi?id=846153

* Tue Jul 24 2012 Gregor Tätzner <brummbq@fedoraproject.org> - 1.3.2-4
- import working lightdm-autologin pam config

* Thu Jul 19 2012 Fedora Release Engineering <rel-eng@lists.fedoraproject.org> - 1.3.2-3
- Rebuilt for https://fedoraproject.org/wiki/Fedora_18_Mass_Rebuild

* Sun Jul 15 2012 Gregor Tätzner <brummbq@fedoraproject.org> - 1.3.2-2
- comply with guidelines concerning user and group handling

* Fri Jul 13 2012 Rex Dieter <rdieter@fedoraproject.org> 1.3.2-1
- lightdm-1.3.2

* Sun Jul 01 2012 Rex Dieter <rdieter@fedoraproject.org> 1.3.1-2
- lightdm.conf: minimum-vt=1 (allows for better plymouth no vt-switch)

* Wed Jun 27 2012 Rex Dieter <rdieter@fedoraproject.org> 1.3.1-1
- lightdm-1.3.1

* Fri Jun 15 2012 Rex Dieter <rdieter@fedoraproject.org> 1.2.2-15
- default to alternatives-provided greeter

* Thu Jun 14 2012 Gregor Tätzner <brummbq@fedoraproject.org> - 1.2.2-14
- check if lightdm user exists, before creating him
- reset patch numbering
- use standard dir perm

* Tue Jun 12 2012 Rex Dieter <rdieter@fedoraproject.org> 1.2.2-13
- Requires: lightdm-greeter = 1.2

* Tue Jun 12 2012 Rex Dieter <rdieter@fedoraproject.org> 1.2.2-12
- move headers into -qt-devel pkg

* Mon Jun 11 2012 Rex Dieter <rdieter@fedoraproject.org> 1.2.2-11
- License: LGPLv3+ and GPLv3+
- make dbus files %%config
- gobject-devel, qt-devel subpkgs

* Mon May 14 2012 Rex Dieter <rdieter@fedoraproject.org> 1.2.2-10
- move /etc/tmpfiles.d/* => /usr/lib/tempfiles.d/

* Wed May 09 2012 Rex Dieter <rdieter@fedoraproject.org> 1.2.2-9
- fix typo, Requires: accountsservice

* Thu Apr 26 2012 Rex Dieter <rdieter@fedoraproject.org> 1.2.2-8
- Requires: accountservice ConsoleKit systemd

* Wed Apr 25 2012 Rex Dieter <rdieter@fedoraproject.org> 1.2.2-7
- respin nodaemon_option patch

* Wed Apr 25 2012 Rex Dieter <rdieter@fedoraproject.org> 1.2.2-6
- Requires: xorg-x11-xinit
- Requires: lightdm-greeter
- -gobject,-qt: drop dep on base pkg (easier for bootstrapping)

* Wed Apr 25 2012 Rex Dieter <rdieter@fedoraproject.org> 1.2.2-5
- make sane default lightdm.conf for fedora
- nodaemon_option.patch
- Requires: xorg-x11-xinit

* Wed Apr 25 2012 Rex Dieter <rdieter@fedoraproject.org> 1.2.2-4
- update lightdm.pam
- make /var/log/lightdm /var/lib/lightdm group-writable too

* Wed Apr 25 2012 Rex Dieter <rdieter@fedoraproject.org> 1.2.2-3
- omit useless %%post(un) scriptlets
- %%pre: add lightdm user/group
- BR: gnome-common
- %%build: --with-greeter-session=lightdm-gtk-greeter (for now)

* Tue Apr 24 2012 Rex Dieter <rdieter@fedoraproject.org> 1.2.2-2
- pkgconfig-style deps

* Tue Apr 24 2012 Rex Dieter <rdieter@fedoraproject.org> 1.2.2-1
- 1.2.2

* Fri Feb 17 2012 Christoph Wickert <cwickert@fedoraproject.org> - 1.1.3-1
- Update to 1.1.3

* Fri Feb 17 2012 Christoph Wickert <cwickert@fedoraproject.org> - 1.0.6-1
- Update to 1.0.6
- Make build verbose

* Sun Oct 02 2011 Christoph Wickert <cwickert@fedoraproject.org> - 1.0.0-1
- Update to 1.0.0

* Wed Aug 17 2011 Christoph Wickert <cwickert@fedoraproject.org> - 0.9.3-1
- Update to 0.9.3

* Fri Jul 08 2011 Christoph Wickert <cwickert@fedoraproject.org> - 0.4.2-1
- Update to 0.4.2

* Sat Jul 02 2011 Christoph Wickert <cwickert@fedoraproject.org> - 0.4.1-1
- Update to 0.4.1

* Sat Jun 25 2011 Christoph Wickert <cwickert@fedoraproject.org> - 0.4.0-1
- Update to 0.4.0

* Fri Apr 22 2011 Christoph Wickert <cwickert@fedoraproject.org> - 0.3.2-1
- Update to 0.3.2

* Sun Jan 23 2011 Christoph Wickert <cwickert@fedoraproject.org> - 0.2.3-1
- Update to 0.2.3

* Sat Oct 23 2010 Christoph Wickert <cwickert@fedoraproject.org> - 0.1.2-1
- Initial package
