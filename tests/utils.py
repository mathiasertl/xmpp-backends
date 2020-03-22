# This file is part of xmpp-backends (https://github.com/mathiasertl/xmpp-backends).
#
# xmpp-backends is free software: you can redistribute it and/or modify it under the terms of the GNU General
# Public License as published by the Free Software Foundation, either version 3 of the License, or (at your
# option) any later version.
#
# xmpp-backends is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the
# implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License
# for more details.
#
# You should have received a copy of the GNU General Public License along with xmpp-backends. If not, see
# <http://www.gnu.org/licenses/>.

import doctest
import re

import six

FORCE_TEXT_FLAG = doctest.register_optionflag('FORCE_TEXT')


class CompatDoctestChecker(doctest.OutputChecker):
    """OutputChecker for py2/py3 compatible unicode strings."""

    def check_output(self, want, got, optionflags):
        if six.PY2 is True and optionflags & FORCE_TEXT_FLAG:
            got = re.sub("u'(.*?)'", "'\\1'", got)
            got = re.sub('u"(.*?)"', '"\\1"', got)

        return doctest.OutputChecker.check_output(self, want, got, optionflags)
