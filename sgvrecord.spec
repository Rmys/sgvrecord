Name:           sgvrecord
Version:        1.0
Release:        1%{?dist}
Summary:        Simple Tool To Record Screen
License:        GPLv3     
URL:            https://github.com/yucefsourani/sgvrecord
Source0:        https://github.com/yucefsourani/sgvrecord/archive/master.zip
BuildArch:      noarch
BuildRequires:  python3-devel
Requires:       pygobject3
Requires:       python3-gobject
Requires:       gtk3
Requires:       gstreamer1
Requires:       gstreamer1-plugins-good
Requires:       gstreamer1-plugins-base
#Requires:       libwnck3
Requires:       alsa-utils
Requires:       pulseaudio-utils

%description
Simple Tool To Record Screen.


%prep
%autosetup -n sgvrecord-master

%build
%{__python3} setup.py build

%install
rm -rf $RPM_BUILD_ROOT
%{__python3} setup.py install -O1 --skip-build --root $RPM_BUILD_ROOT --prefix /usr


%files
%doc README.md
%{python3_sitelib}/*
%{_bindir}/sgvrecord.py
%{_datadir}/applications/*
%{_datadir}/pixmaps/*
%{_datadir}/icons/hicolor/*/apps/*
%{_datadir}/doc/sgvrecord/LICENSE

%changelog
* Tue Oct 30 2018 yucuf sourani <youssef.m.sourani@gmail.com> 1.0-1
- Initial For Fedora 
