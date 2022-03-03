#!/usr/bin/env bash

#
# Version maintenance script.
#
# @author Matthew Casey
#
# (c) Digital Content Analysis Technology Ltd 2022
#

#
# Use this script to maintain the SDK version number.
#
# The SDK version has the format `<major>.<minor>.<patch>` where
# - `major` is the major version number which indicates major breaking changes between versions
# - `minor` is the minor version number which introduces backwards-compatible changes
# - `patch` is the patch version number which introduces bug fixes
#
# Whenever the `minor` number changes, the `patch` number is reset to `0`. Similarly, when the `major` number changes, the `minor` and
# `patch` numbers are reset to `0`. Each version change is also associated with the date and time of when it was changed.
#
# Usage:
#   version.sh <major|minor|patch>
#
# where the argument should be:
#
# - `major` to increase the `major` version number by 1
# - `minor` to increase the `minor` version number by 1
# - `patch` to increase the `patch` version number by 1
#
# Whenever any of the version numbers are changed, the version date is also changed.
#

# Check the input argument.
change=""

if [ "$1" != "" ]; then
  change=$1
else
  echo "Usage: $(basename "$0") <major|minor|patch>"
  exit 1
fi

# Extract the version number from the file.
version_file="fusion_platform/__init__.py"
prefix="__version__ = '"
suffix="'"
version=$(grep "$prefix" $version_file)
version=${version#$prefix}
version=${version%$suffix}

IFS="."
parts=($version)
unset IFS

major=''
minor=''
patch=''

for i in "${parts[@]}"; do
  if [ "$major" == "" ]; then
    major="$i"
  elif [ "$minor" == "" ]; then
    minor="$i"
  elif [ "$patch" == "" ]; then
    patch="$i"
  fi
done

echo "Found version $major.$minor.$patch"

# Now upgrade the relevant version.
case $change in
major)
  major="$((major + 1))"
  minor=0
  patch=0
  ;;

minor)
  minor="$((minor + 1))"
  patch=0
  ;;

patch)
  patch="$((patch + 1))"
  ;;
esac

# And save it back to the file.
echo "Upgrading $change version to $major.$minor.$patch"
sed -i '' "s/^__version__.*/__version__ = '$major.$minor.$patch'/g" $version_file

timestamp=$(date -u +%FT%TZ)
sed -i '' "s/^__version_date__.*/__version_date__ = '$timestamp'/g" $version_file
