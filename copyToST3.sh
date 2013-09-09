#!/bin/bash
#
# MAC ONLY: This script does the following:
# 1. Deletes your sublime text 3 CSSLint.sublime-package file from Installed Packages
# 2. Creates a new CSSLint.sublime-package of the current directory and 
# 	 places it in your ST3 Installed Packages folder
# WARNING: This must only be used in the CSSLint project folder. It will break
# 		   if used elsewhere (without proper modification)
# WARNING: This is for testing only.
# WARNING: Package Control may overwrite this file when ST3 is first launched.
# WARNING: This script is for use on OSX only.

PACKAGE_PATH='Library/Application Support/Sublime Text 3/Installed Packages/CSSLint.sublime-package'

# Delete CSSLint.sublime-package in ST3
echo 'Deleting ~/'${PACKAGE_PATH}
rm ~/"${PACKAGE_PATH}"

# Create a new zip file and copy it to ST3
echo 'Creating new CSSLint.sublime-package into ~/'${PACKAGE_PATH}
zip -r ~/"${PACKAGE_PATH}" --exclude=*.git* --exclude=*.pyc* .

