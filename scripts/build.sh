#!/usr/bin/env bash

#
# Build script.
#
# @author Matthew Casey
#
# (c) Digital Content Analysis Technology Ltd 2022
#

#
# Use this script to build the SDK package ready for deployment.
#
# Usage:
#   build.sh
#

# Determine the OS and set the sed command appropriately.
if [[ $OSTYPE == 'darwin'* ]]; then
  sedi=(sed -i '')
else
  sedi=(sed -i)
fi

# We are about to build so increase the patch number automatically.
version_output=$(scripts/version.sh patch)
echo $version_output
version=$(echo $version_output | tail -1 | rev | cut -d' ' -f 1 | rev)

# Update the version in the setup file.
"${sedi[@]}" "s/version=.*,/version='$version',/g" setup.py

# Make sure the translations are up-to-date.
PYTHONPATH=$(pwd) python fusion_platform/localisations.py

# Now build the documentation. This assumes that we have the engine translations file locally.
PYTHONPATH=$(pwd) python fusion_platform/documentation.py "../engine/engine/translations.py"

rm -rf docs/fusion_platform
pdoc --html --config show_inherited_members=True --output-dir docs --template-dir docs/template fusion_platform

# Delete any existing builds.
rm -rf build
rm -rf dist
rm -rf fusion_platform_python_sdk.egg-info

# Now build the distribution.
python setup.py sdist bdist_wheel

# Remove any of the build files.
rm -rf build
rm -rf fusion_platform_python_sdk.egg-info

# Finally, check the built distributions.
twine check dist/*