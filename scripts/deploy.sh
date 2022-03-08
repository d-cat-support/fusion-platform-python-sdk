#!/usr/bin/env bash

#
# Deployment script.
#
# @author Matthew Casey
#
# (c) Digital Content Analysis Technology Ltd 2022
#

#
# Use this script to deploy the package to GitHub and PyPI.
#
# Usage:
#   deploy.sh [test]
#
# where
#
# - `test` signifies that this is a test deployment to TestPyPI only. No push will be made to GitHib.
#

# Update the GitHub repository with the current version.
if [ "$1" == "" ]; then
  # Create a temporary clone of the repository.
  rm -rf /tmp/fusion-platform-python-sdk
  git clone git@github-support.com:d-cat-support/fusion-platform-python-sdk.git /tmp/fusion-platform-python-sdk

  # Update the version with the latest release.
  mkdir -p /tmp/fusion-platform-python-sdk/docs/
  cp -r ./docs/ /tmp/fusion-platform-python-sdk/docs/

  mkdir -p /tmp/fusion-platform-python-sdk/fusion_platform/
  cp -r ./fusion_platform/ /tmp/fusion-platform-python-sdk/fusion_platform/

  mkdir -p /tmp/fusion-platform-python-sdk/resources/
  cp -r ./resources/ /tmp/fusion-platform-python-sdk/resources/

  mkdir -p /tmp/fusion-platform-python-sdk/scripts/
  cp -r ./scripts/ /tmp/fusion-platform-python-sdk/scripts/

  mkdir -p /tmp/fusion-platform-python-sdk/tests/
  cp -r ./tests/ /tmp/fusion-platform-python-sdk/tests/

  cp .gitignore /tmp/fusion-platform-python-sdk/
  cp LICENSE.txt /tmp/fusion-platform-python-sdk/
  cp MANIFEST.in /tmp/fusion-platform-python-sdk/
  cp pytest.ini /tmp/fusion-platform-python-sdk/
  cp README.md /tmp/fusion-platform-python-sdk/
  cp requirements.txt /tmp/fusion-platform-python-sdk/
  cp setup.py /tmp/fusion-platform-python-sdk/

  # Remove anything that we do not want in the repository.
  find /tmp/fusion-platform-python-sdk -name "*.docx" -type f -delete
  find /tmp/fusion-platform-python-sdk -name "*.DS_Store" -type f -delete
  find /tmp/fusion-platform-python-sdk -name "__pycache__" -type d -print0 | xargs -0 -I {} /bin/rm -rf "{}"

  # Get the current version.
  version_file="fusion_platform/__init__.py"
  prefix="__version__ = '"
  suffix="'"
  version=$(grep "$prefix" $version_file)
  version=${version#$prefix}
  version=${version%$suffix}

  # Add all files to the commit, commit and push.
  (cd /tmp/fusion-platform-python-sdk && git add . && git commit -m "Latest release" && git push && git tag "$version" && git push origin "$version")

  # Clean up.
  rm -rf /tmp/fusion-platform-python-sdk
fi

deployment_command=(twine upload)

# Check the input arguments and build the deployment command options.
if [ "$1" != "" ]; then
  deployment_command+=(--repository testpypi)
fi

deployment_command+=("dist/*")

# Deploy the built packages.
echo "${deployment_command[@]}"
"${deployment_command[@]}"
