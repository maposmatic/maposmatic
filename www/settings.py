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
import os.path

from django.conf.global_settings import TEMPLATE_CONTEXT_PROCESSORS
from django.utils.translation import ugettext_lazy as _

from settings_local import *

PROJECT_PATH = os.path.dirname(os.path.abspath(__file__))

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

TEMPLATE_DIRS = (
    os.path.join(PROJECT_PATH, 'templates'),
)

LOCAL_MEDIA_PATH = os.path.join(PROJECT_PATH, 'media')

INSTALLED_APPS = (
    'django.contrib.sessions',
    'www.maposmatic',
)

# Available website translations. Note that the language codes must be
# specified in Django i18n location (all lowercase, with the language and
# locale separated by a dash instead of an underscore: pt_BR -> pt-br)
LANGUAGES = (("fr", u"Français"),
             ("en", u"English"),
             ("de", u"Deutsch"),
             ("it", u"Italiano"),
             ("ca", u"Català"),
             ("ru", u"Русский"),
             ("ar", u"العربية"),
             ("pt-br", u"Português do Brasil"),
             ("nb", u"Norwegian Bokmål"),
             ("nl", u"Nederlands"),
             ("hr-hr", u"Hrvatski"),
             ("pl", u"Polski"),
             ("es", u"Español"))

MAP_LANGUAGES = [("fr_BE.UTF-8", u"Royaume de Belgique (FR)"),
                 ("fr_FR.UTF-8", u"France"),
                 ("fr_CA.UTF-8", u"Canada (FR)"),
                 ("fr_CH.UTF-8", u"Suisse (FR)"),
                 ("fr_LU.UTF-8", u"Luxembourg (FR)"),
                 ("en_AG",       u"Antigua and Barbuda (EN)"),
                 ("en_AU.UTF-8", u"Australia (EN)"),
                 ("en_BW.UTF-8", u"Botswana (EN)"),
                 ("en_CA.UTF-8", u"Canada (EN)"),
                 ("en_DK.UTF-8", u"Denmark (EN)"),
                 ("en_GB.UTF-8", u"United Kingdom (EN)"),
                 ("en_HK.UTF-8", u"Hong Kong (EN)"),
                 ("en_IE.UTF-8", u"Ireland (EN)"),
                 ("en_IN",       u"India (EN)"),
                 ("en_NG",       u"Nigeria (EN)"),
                 ("en_NZ.UTF-8", u"New Zealand (EN)"),
                 ("en_PH.UTF-8", u"Philippines (EN)"),
                 ("en_SG.UTF-8", u"Singapore (EN)"),
                 ("en_US.UTF-8", u"United States (EN)"),
                 ("en_ZA.UTF-8", u"South Africa (EN)"),
                 ("en_ZW.UTF-8", u"Zimbabwe (EN)"),
                 ("de_BE.UTF-8", u"Königreich Belgien (DE)"),
                 ("it_CH.UTF-8", u"Svizzera (IT)"),
                 ("it_IT.UTF-8", u"Italia (IT)"),
                 ("nb_NO.UTF-8", u"Norwegian Bokmål (NO)"),
                 ("nl_BE.UTF-8", u"Koninkrijk België (NL)"),
                 ("nl_NL.UTF-8", u"Nederland (NL)"),
                 ("de_AT.UTF-8", u"Österreich (DE)"),
                 ("de_DE.UTF-8", u"Deutschland (DE)"),
                 ("de_LU.UTF-8", u"Luxemburg (DE)"),
                 ("de_CH.UTF-8", u"Schweiz (DE)"),
                 ("ca_ES.UTF-8", u"Espanya (CA)"),
                 ("ca_AD.UTF-8", u"Andorra (CA)"),
                 ("ca_FR.UTF-8", u"França (CA)"),
                 ("pt_BR.UTF-8", u"Brasil (PT)"),
                 ("da_DK.UTF-8", u"Danmark (DA)"),
                 ("hr_HR.UTF-8", u"Republika Hrvatska"),
                 ("pl_PL.UTF-8", u"Rzeczpospolita Polska"),
                 ("es_ES.UTF-8", u"España (ES)"),
                 ("es_AR.UTF-8", u"Argentina (ES)"),
                 ("es_BO.UTF-8", u"Bolivia (ES)"),
                 ("es_CL.UTF-8", u"Chile (ES)"),
                 ("es_CR.UTF-8", u"Costa Rica (ES)"),
                 ("es_DO.UTF-8", u"República Dominicana (ES)"),
                 ("es_EC.UTF-8", u"Ecuador (ES)"),
                 ("es_SV.UTF-8", u"El Salvador (ES)"),
                 ("es_GT.UTF-8", u"Guatemala (ES)"),
                 ("es_HN.UTF-8", u"Honduras (ES)"),
                 ("es_MX.UTF-8", u"México (ES)"),
                 ("es_NI.UTF-8", u"Nicaragua (ES)"),
                 ("es_PA.UTF-8", u"Panamá (ES)"),
                 ("es_PY.UTF-8", u"Paraguay (ES)"),
                 ("es_PE.UTF-8", u"Perú (ES)"),
                 ("es_PR.UTF-8", u"Puerto Rico (ES)"),
                 ("es_US.UTF-8", u"Estados Unidos de América (ES)"),
                 ("es_UY.UTF-8", u"Uruguay (ES)"),
                 ("es_VE.UTF-8", u"Venezuela (ES)"),
                 ("ar_DZ.UTF-8", u"الجزائر (AR)"),
                 ("ar_BH.UTF-8", u"البحرين (AR)"),
                 ("ar_EG.UTF-8", u"مصر (AR)"),
                 ("ar_IQ.UTF-8", u"العراق (AR)"),
                 ("ar_JO.UTF-8", u"الأردنّ‎ (AR)"),
                 ("ar_KW.UTF-8", u"الكويت (AR)"),
                 ("ar_LB.UTF-8", u"لبنان (AR)"),
                 ("ar_LY.UTF-8", u"ليبيا (AR)"),
                 ("ar_MA.UTF-8", u"المملكة المغربية (AR)"),
                 ("ar_OM.UTF-8", u"سلطنة عمان (AR)"),
                 ("ar_QA.UTF-8", u"دولة قطر (AR)"),
                 ("ar_SA.UTF-8", u"المملكة العربية السعودية (AR)"),
                 ("ar_SD.UTF-8", u"السودان (AR)"),
                 ("ar_SY.UTF-8", u"سوريا (AR)"),
                 ("ar_TN.UTF-8", u"تونس (AR)"),
                 ("ar_AE.UTF-8", u"دولة الإمارات العربية المتحدة (AR)"),
                 ("ar_YE.UTF-8", u"اليَمَن (AR)")]

MAP_LANGUAGES.sort(lambda x, y: cmp(x[1], y[1]))
# "C" must be the last entry
MAP_LANGUAGES.append(("C", _(u"No localization")))

# Logging
LOG = logging.getLogger(os.environ.get("MAPOSMATIC_LOG_TARGET",
                                       "maposmatic"))
LOG.setLevel(int(os.environ.get("MAPOSMATIC_LOG_LEVEL",
                                DEFAULT_MAPOSMATIC_LOG_LEVEL)))
_log_dest = os.environ.get('MAPOSMATIC_LOG_FILE', DEFAULT_MAPOSMATIC_LOG_FILE)
if _log_dest:
    _fh = logging.FileHandler(_log_dest)
else:
    _fh = logging.StreamHandler()
_fh.setFormatter(logging.Formatter(os.environ.get("MAPOSMATIC_LOG_FORMAT",
                                                  DEFAULT_MAPOSMATIC_LOG_FORMAT)))

LOG.addHandler(_fh)
LOG.info("log restarted.")

# GIS database (read settings from OCitySMap's configuration)
import ConfigParser
gis_config = ConfigParser.SafeConfigParser()

if OCITYSMAP_CFG_PATH is None:
    OCITYSMAP_CFG_PATH = os.path.expanduser('~/.ocitysmap.conf')
with open(OCITYSMAP_CFG_PATH) as fp:
    gis_config.readfp(fp)
GIS_DATABASE_HOST = gis_config.get('datasource', 'host')
GIS_DATABASE_USER = gis_config.get('datasource', 'user')
GIS_DATABASE_PASSWORD = gis_config.get('datasource', 'password')
GIS_DATABASE_NAME = gis_config.get('datasource', 'dbname')

def has_gis_database():
    return GIS_DATABASE_NAME and GIS_DATABASE_NAME != ''

# Job page refresh frequency, in seconds, for when the job is waiting in queue
# and when the job is currently being rendered.
REFRESH_JOB_WAITING = 10
REFRESH_JOB_RENDERING = 20

def is_daemon_running():
    return os.path.exists(MAPOSMATIC_PID_FILE)
