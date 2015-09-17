##########################################################################
# Machination
# Copyright (c) 2014, Alexandre ACEBEDO, All rights reserved.
#
# This library is free software; you can redistribute it and/or
# modify it under the terms of the GNU Lesser General Public
# License as published by the Free Software Foundation; either
# version 3.0 of the License, or (at your option) any later version.
#
# This library is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# Lesser General Public License for more details.
#
# You should have received a copy of the GNU Lesser General Public
# License along with this library.
##########################################################################
import sys
import logging
from logging import Handler
from colorlog import ColoredFormatter
import thread
import re

from progressbar import AnimatedMarker, Bar, BouncingBar, Counter, ETA, \
    FormatLabel, Percentage, ProgressBar, RotatingMarker, Timer, AdaptiveETA
  
COMMANDLINELOGGER = None
REGISTRYLOGGER = None
CORELOGGER = None
FILEGENERATORLOGGER = None
PROVISIONERSLOGGER = None
PROVIDERSLOGGER = None
ROOTLOGGER = None
PROGRESSBARLOGGER = None


def initLoggers():
  formatter = ColoredFormatter("%(log_color)s%(levelname)-8s%(reset)s %(blue)s%(message)s",
                               datefmt=None,
                               reset=True,
                               log_colors={
                                       'DEBUG':    'cyan',
                                       'INFO':     'white',
                                       'WARNING':  'yellow',
                                       'ERROR':    'red',
                                       'CRITICAL': 'red,bg_white',
                               },
                               secondary_log_colors={},
                               style='%'
                               )
  
  #global PROGRESSBARHANDLER
  #PROGRESSBARHANDLER.setFormatter(formatter)

  handler = logging.StreamHandler()
  handler.setFormatter(formatter)

  global ROOTLOGGER
  ROOTLOGGER = logging.getLogger("machination")
  ROOTLOGGER.addHandler(handler)
  
  global COMMANDLINELOGGER
  COMMANDLINELOGGER = logging.getLogger("machination.cmdline")

  global REGISTRYLOGGER
  REGISTRYLOGGER = logging.getLogger("machination.registries")

  global CORELOGGER
  CORELOGGER = logging.getLogger("machination.core")

  global FILEGENERATORLOGGER
  FILEGENERATORLOGGER = logging.getLogger("machination.filegenerator")

  global PROVISIONERSLOGGER
  PROVISIONERSLOGGER = logging.getLogger("machination.provisioners")
  
  global PROVIDERSLOGGER
  PROVIDERSLOGGER = logging.getLogger("machination.providers")

  global PROGRESSBARLOGGER
  PROGRESSBARLOGGER = logging.getLogger("progressbar")
  PROGRESSBARLOGGER.setLevel(logging.INFO)
    
def setLogLevel(lvl):
  global logHandler
  ROOTLOGGER.setLevel(lvl)
  #PROGRESSBARHANDLER.setLevel(lvl)