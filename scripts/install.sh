#!/usr/bin/env bash

#
# Install script.
#
# @author Matthew Casey
#
# (c) Digital Content Analysis Technology Ltd 2024
#

#
# Use this script to install all the required packages. Note, this assumes that a virtual environment for the correct version of Python is available.
#
# Usage:
#   install.sh
#

# Upgrade pip.
pip install pip --upgrade

# Now install everything needed for development.
pip install -r requirements.txt
