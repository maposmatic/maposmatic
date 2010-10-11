# coding: utf-8

# maposmatic, the web front-end of the MapOSMatic city map generation system
# Copyright (C) 2010  David Decotigny
# Copyright (C) 2010  Frédéric Lehobey
# Copyright (C) 2010  Pierre Mauduit
# Copyright (C) 2010  David Mentré
# Copyright (C) 2010  Maxime Petazzoni
# Copyright (C) 2010  Thomas Petazzoni
# Copyright (C) 2010  Gaël Utard

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

# Logging configuration
import logging

if not hasattr(logging, 'maposmatic_logging_setup_done'):
    logging.maposmatic_logging_setup_done = False

def setup_maposmatic_logging(level, destination, log_format):
    if logging.maposmatic_logging_setup_done:
        return

    maposmatic_logger = logging.getLogger('maposmatic')
    maposmatic_logger.setLevel(level)

    ocitysmap_logger = logging.getLogger('ocitysmap')
    ocitysmap_logger.setLevel(level)

    if destination:
        handler = logging.FileHandler(destination)
    else:
        handler = logging.StreamHandler()

    handler.setFormatter(logging.Formatter(log_format))
    maposmatic_logger.addHandler(handler)
    ocitysmap_logger.addHandler(handler)

    maposmatic_logger.info('log restarted.')
    logging.maposmatic_logging_setup_done = True
