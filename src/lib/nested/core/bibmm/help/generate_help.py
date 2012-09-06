# -*- coding:utf-8 -*-
#
# Copyright (C) 2011, 2012 Carlos Jenkins <carlos@jenkins.co.cr>
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

"""
Generate help based on BibTeX definition.

To generate help on your language first translate Nested to your language:

    https://www.transifex.com/projects/p/nested/

Make sure you have those locales in a gettext reachable location.

Then, run this script using the locale you want to generate:

    user@computer: LANG=en_US python generate_help.py

"""

from nested import *

import os
import logging
import gettext

from shutil import rmtree
from os import remove, makedirs
from os.path import join, isfile, isdir, exists

from nested.core.bibmm.bibtexdef import bibtex_fields_desc, bibtex_fields, bibtex_entries

WHERE_AM_I = os.path.get_module_path(__file__)
logger = logging.get_logger(__name__)
_ = gettext.translation().gettext

# Translatable base strings
_format = _('Format')
_citation_key_token = _('citation_key')
_required_fields_token = _('required_fields')
_optional_fields_token = _('optional_fields')
_required_fields = _('Required fields')
_optional_fields = _('Optional fields')
_field_text_token = _('field_text')
_entry_title = _('{entry} entry')
_field_title = _('{field} field')

###########
# BASE
###########
base_template = '''\
<?xml version="1.0"
      encoding="{encoding}"
?>
<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Strict//EN" "http://www.w3.org/TR/xhtml1/DTD/xhtml1-strict.dtd">
<html xmlns="http://www.w3.org/1999/xhtml">
<head>
<title>Help On BibTeX {_title}</title>
    <meta http-equiv="Content-Type" content="text/html"; charset="{encoding}">
    <link rel="stylesheet" type="text/css" href="../style.css" />
</head>
<body>
<div class="wrapper">

<h1 class="title">{_title}</h1>

{body}

</div>
</body>
</html>
'''

###########
# ENTRY
###########
entry_template = '''\
<p>{_description}</p>

<p>{_format}:</p>

<pre>
    @{entry}{{{_citation_key_token},
            {_required_fields_token} [, {_optional_fields_token}] }}
</pre>

<p>{_required_fields}:
{required_fields}
</p>

<p>{_optional_fields}:
{optional_fields}
</p>
'''

entry_field_template = '''\
<a class="field" href="field_{field}.html">{field}</a>\
'''

###########
# FIELD
###########
field_template = '''\
<p>{_description}<p>

<p>{_format}:</p>
<pre>
    {field} = "{_field_text_token}"
</pre>
'''

###########
# GENERATOR
###########
if __name__ == '__main__':

    # Create entry documents
    output = join(WHERE_AM_I, context_lang)
    if isfile(output):
        os.remove(output)
    elif isdir(output):
        rmtree(output)
    elif exists(output):
        print('Error, unable to write {}'.format(output))
        exit(-1)
    makedirs(output)

    # Create entries help
    for key, value in bibtex_entries.items():

        # Format fields for entry
        def _format_fields(cls):
            fields = []
            for i in value[cls]:
                for j in i.split('/'):
                    fields.append(
                            entry_field_template.format(field=j)
                        )
            return ', '.join(fields) + '.'

        required_fields = _format_fields('required')
        optional_fields = _format_fields('optional')

        # Format entry
        body = entry_template.format(
                _description=value['comment'],
                _format=_format,
                entry=key.upper(),
                _citation_key_token=_citation_key_token,
                _required_fields_token=_required_fields_token,
                _optional_fields_token=_optional_fields_token,
                _required_fields=_required_fields,
                _optional_fields=_optional_fields,
                required_fields=required_fields,
                optional_fields=optional_fields,
            )
        content = base_template.format(body=body,
                                _title=_entry_title.format(entry=key),
                                encoding='UTF-8')

        # Save entry help
        output_file = join(output, 'entry_' + key + '.html')
        with open(output_file, 'w') as handler:
            handler.write(content)

    # Create fields help
    for key, value in bibtex_fields_desc.items():

        # Format field
        body = field_template.format(
                _description=value,
                _format=_format,
                field=key,
                _field_text_token=_field_text_token,
            )
        content = base_template.format(body=body,
                                _title=_field_title.format(field=key),
                                encoding='UTF-8')

        # Save entry help
        output_file = join(output, 'field_' + key + '.html')
        with open(output_file, 'w') as handler:
            handler.write(content)
