# coding: utf-8

# maposmatic, the web front-end of the MapOSMatic city map generation system
# Copyright (C) 2009  David Decotigny
# Copyright (C) 2009  Frédéric Lehobey
# Copyright (C) 2009  David Mentré
# Copyright (C) 2009  Maxime Petazzoni
# Copyright (C) 2009  Thomas Petazzoni
# Copyright (C) 2009  Gaël Utard

# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as
# published by the Free Software Foundation, either version 3 of the
# License, or any later version.

# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.

# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

# Django settings for www project.

import logging
from settings_local import *
from django.utils.translation import ugettext_lazy as _

TEMPLATE_DEBUG = DEBUG

MANAGERS = ADMINS

# Local time zone for this installation. Choices can be found here:
# http://en.wikipedia.org/wiki/List_of_tz_zones_by_name
# although not all choices may be available on all operating systems.
# If running in a Windows environment this must be set to the same as your
# system time zone.
TIME_ZONE = 'Europe/Paris'

# Language code for this installation. All choices can be found here:
# http://www.i18nguy.com/unicode/language-identifiers.html
LANGUAGE_CODE = 'en-us'

SITE_ID = 1

# If you set this to False, Django will make some optimizations so as not
# to load the internationalization machinery.
USE_I18N = True

# Absolute path to the directory that holds media.
# Example: "/home/media/media.lawrence.com/"
MEDIA_ROOT = ''

# URL that handles the media served from MEDIA_ROOT. Make sure to use a
# trailing slash if there is a path component (optional in other cases).
# Examples: "http://media.lawrence.com", "http://example.com/media/"
MEDIA_URL = ''

# URL prefix for admin media -- CSS, JavaScript and images. Make sure to use a
# trailing slash.
# Examples: "http://foo.com/media/", "/media/".
ADMIN_MEDIA_PREFIX = '/media/'

# Make this unique, and don't share it with anybody.
SECRET_KEY = 'tm+wb)lp5q%br=p0d2toz&km_-w)cmcelv!7inons&^v9(q!d2'

# List of callables that know how to import templates from various sources.
TEMPLATE_LOADERS = (
    'django.template.loaders.filesystem.load_template_source',
    'django.template.loaders.app_directories.load_template_source',
#     'django.template.loaders.eggs.load_template_source',
)

from django.conf.global_settings import TEMPLATE_CONTEXT_PROCESSORS

TEMPLATE_CONTEXT_PROCESSORS += (
     'django.core.context_processors.request',
     'www.maposmatic.context_processors.all',
)

MIDDLEWARE_CLASSES = (
    'django.middleware.common.CommonMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.locale.LocaleMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
)

ROOT_URLCONF = 'www.urls'

import os.path

PROJECT_PATH = os.path.dirname(os.path.abspath(__file__))

TEMPLATE_DIRS = (
    os.path.join(PROJECT_PATH, 'templates'),
)

LOCAL_MEDIA_PATH = os.path.join(PROJECT_PATH, 'media')

INSTALLED_APPS = (
    'django.contrib.sessions',
    'www.maposmatic',
)

formatter = logging.Formatter("%(name)s - %(asctime)s - %(levelname)s - %(message)s")

LANGUAGES = (("fr", u"Français"),
             ("en", u"English"),
             ("de", u"Deutsch"),
             ("it", u"Italiano"),
             ("ca", u"Català"))

MAP_LANGUAGES = [("fr_BE.UTF-8", u"Royaume de Belgique (FR)"),
                 ("fr_FR.UTF-8", u"France"),
                 ("fr_CA.UTF-8", u"Canada (FR)"),
                 ("fr_CH.UTF-8", u"Suisse (FR)"),
                 ("fr_LU.UTF-8", u"Luxembourg (FR)"),
                 ("en_AG", u"Antigua and Barbuda (EN)"),
                 ("en_AU.UTF-8", u"Australia (EN)"),
                 ("en_BW.UTF-8", u"Botswana (EN)"),
                 ("en_CA.UTF-8", u"Canada (EN)"),
                 ("en_DK.UTF-8", u"Denmark (EN)"),
                 ("en_GB.UTF-8", u"United Kingdom (EN)"),
                 ("en_HK.UTF-8", u"Hong Kong (EN)"),
                 ("en_IE.UTF-8", u"Ireland (EN)"),
                 ("en_IN", u"India (EN)"),
                 ("en_NG", u"Nigeria (EN)"),
                 ("en_NZ.UTF-8", u"New Zealand (EN)"),
                 ("en_PH.UTF-8", u"Philippines (EN)"),
                 ("en_SG.UTF-8", u"Singapore (EN)"),
                 ("en_US.UTF-8", u"United States (EN)"),
                 ("en_ZA.UTF-8", u"South Africa (EN)"),
                 ("en_ZW.UTF-8", u"Zimbabwe (EN)"),
                 ("de_BE.UTF-8", u"Königreich Belgien (DE)"),
                 ("it_CH.UTF-8", u"Svizzera (IT)"),
                 ("it_IT.UTF-8", u"Italia (IT)"),
                 ("nl_BE.UTF-8", u"Koninkrijk België (NL)"),
                 # "C" must be the last entry
                 ("C", _(u"No localization"))]

LOG = logging.getLogger(os.environ.get("MAPOSMATIC_LOG_TARGET",
                                       "maposmatic"))
LOG.setLevel(os.environ.get("MAPOSMATIC_LOG_LEVEL",
                            DEFAULT_MAPOSMATIC_LOG_LEVEL))
try:
    _fh = logging.FileHandler(os.environ.get('MAPOSMATIC_LOG_FILE',
                                             DEFAULT_MAPOSMATIC_LOG_FILE))
except KeyError:
    _fh = logging.FileHandler('maposmatic.log')

LOG.addHandler(_fh)
LOG.info("log restarted.")

ITEMS_PER_PAGE = 25

def has_gis_database():
    return GIS_DATABASE_NAME and GIS_DATABASE_NAME != ''
