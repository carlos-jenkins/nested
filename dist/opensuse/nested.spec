#
# spec file for package nested
#
# Copyright (c) 2011 Izaac Zavaleta
# Copyright (c) 2012 SUSE LINUX Products GmbH, Nuernberg, Germany.
#
# All modifications and additions to the file contributed by third parties
# remain the property of their copyright owners, unless otherwise agreed
# upon. The license for this file, and modifications and additions to the
# file, is the same license as for the pristine package itself (unless the
# license for the pristine package is not an Open Source License, in which
# case the license is the MIT License). An "Open Source License" is a
# license that conforms to the Open Source Definition (Version 1.9)
# published by the Open Source Initiative.

# Please submit bugfixes or comments via http://bugs.opensuse.org/
#


Name:           nested
Version:        1.2.2
Release:        12.1
License:        GPL-2.0+ and Apache-2.0
Summary:        Specialized editor for structured documents
Url:            http://nestededitor.sourceforge.net/
Group:          Productivity/Editors/Other
Source0:        http://downloads.sourceforge.net/project/nestededitor/%{name}-%{version}.tar.gz
Source1:        %{name}.desktop
BuildRequires:  fdupes
BuildRequires:  python-devel
BuildRequires:  update-desktop-files
BuildRoot:      %{_tmppath}/%{name}-%{version}-build
%if 0%{?suse_version} >= 1210
BuildRequires:  python-distribute
%endif
Requires:       netpbm
Requires:       python-gtk
Requires:       python-webkitgtk
Requires:       texlive
Requires:       texlive-latex
%if 0%{?suse_version} && 0%{?suse_version} <= 1110
%{!?python_sitelib: %global python_sitelib %(python -c "from distutils.sysconfig import get_python_lib; print get_python_lib()")}
%else
BuildArch:      noarch
%endif

%description
Nested is a specialized editor focused on creating structured documents such as reports, publications, presentations, books, etc. It is designed to help the user concentrate on writing content without been distracted by format or markup. It offers a rich WYSIWYM interface where the user writes plain text with a lightweight markup language.

%prep
%setup -q

%build
python setup.py build

%install
python setup.py install --prefix=%{_prefix} --root=%{buildroot}
mkdir -p %{buildroot}%{_datadir}/applications/
cp %{SOURCE1} %{buildroot}%{_datadir}/applications/
mkdir -p %{buildroot}%{_datadir}/pixmaps/
python l10n/compile_mo.py
mkdir -p %{buildroot}%{_datadir}/locale
mv l10n/mo/* %{buildroot}%{_datadir}/locale
mkdir -p %{buildroot}%{_mandir}/man1
python -B %{_builddir}/%{name}-%{version}/nested/txt2tags.py --target man \
    --infile %{_builddir}/%{name}-%{version}/nested/examples/Manpage/Manpage.t2t \
    --outfile %{_builddir}/%{name}-%{version}/nested/nested.1
cp -p %{_builddir}/%{name}-%{version}/nested/nested.1 %{buildroot}%{_mandir}/man1
%if 0%{?suse_version} < 1210
cp %{buildroot}%{python_sitelib}/nested/nested.png %{buildroot}%{_datadir}/pixmaps/
%else
mv %{buildroot}%{python_sitelib}/nested/nested.png %{buildroot}%{_datadir}/pixmaps/
%endif
%suse_update_desktop_file %{buildroot}%{_datadir}/applications/%{name}.desktop
%fdupes %{buildroot}%{python_sitelib}/nested/
%find_lang %{name}

%files -f %name.lang
%defattr(-,root,root,-)
%doc CHANGELOG.txt LICENSE.txt
%{_bindir}/nested
%{_datadir}/applications/nested.desktop
%{_datadir}/pixmaps/nested.png
%{_datadir}/locale/*/LC_MESSAGES/%{name}.mo
%{python_sitelib}/*
%{_mandir}/man1/%{name}.1.*

%changelog
* Wed Jan 25 2012 saschpe@suse.de
- Spec cleanup:
  * Reduce unneeded macro usage
  * Removed outdated %%clean section
  * Fix some rpmlint issues (%%find_lang)
- Removed scary service files
* Thu Jan 12 2012 cfarrell@suse.com
- license update: GPL-2.0+ and Apache-2.0
  There are numerous Apache-2.0 licensed javascript files
* Wed Jan 11 2012 jorge.izaac@gmail.com
- added man page fix
* Fri Dec 30 2011 jorge.izaac@gmail.com
- fixed distro version check in first BuildRequires
- moved texlive and netpbm from BuildRequires to Requires
* Thu Dec 29 2011 jorge.izaac@gmail.com
- including pyo files as per http://fedoraproject.org/wiki/Packaging:Python#Files_to_include
* Thu Dec 29 2011 jorge.izaac@gmail.com
- opensuse 11.3 uses python 2.6 so egg-info needs to be explicitly added
* Wed Dec 28 2011 jorge.izaac@gmail.com
- exception cases for older opensuse versions
* Wed Dec 28 2011 jorge.izaac@gmail.com
- fixed missing directories rpm ownership
* Wed Dec 28 2011 jorge.izaac@gmail.com
- no more warnings of files listed twice
- more verbosity in %%files section
- %%fdupes pointing to wrong location. FIXED
- added tex libraries to Requires
* Tue Dec 27 2011 jorge.izaac@gmail.com
- wrong source filename in spec file fixed
* Tue Dec 27 2011 jorge.izaac@gmail.com
- changed source code compression method
* Tue Dec 27 2011 jorge.izaac@gmail.com
- distro version control in some statements
- updated rpmlintrc adding filter for suse_update_desktop_file
* Tue Dec 27 2011 jorge.izaac@gmail.com
- added nested.rpmlintrc to filter known warnings
- missing update-desktop-files in BuildRequires
- changed png dinamically in spec also some syntax clean up
- rpmlint checks passed
- fixed numerous listed twice files warnings
- CHANGELOG.txt and LICENSE.txt added to %%doc
- python-distribute not present in suse_version < 1210
