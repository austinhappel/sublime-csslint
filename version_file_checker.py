import os
from hashlib import sha256
from pprint import pprint

FILE_LIST = [
    os.path.join('scripts/csslint/csslint-rhino.js'),
    os.path.join('scripts/rhino/js.jar'),
]

def generate_sha256(file_path, block_size=1024):
    """Generates a sha256 checksum of the file passed in."""

    if os.path.exists(file_path):
        f = open(file_path, 'rb')
        hash = sha256()

        while True:
            data = f.read(block_size)
            if not data:
                break
            
            hash.update(data)

        return hash.hexdigest()
    else:
        return False

    
def check_file_match(file_list, path_prefix=''):
    """
    Takes an array of file path/checksum objects and verifies that 
    the checksum matches the file in the target_dir.
    """
    ret = []

    for file_details in file_list:
        fp = os.path.join(path_prefix, file_details['file_path'])
        hash = file_details['checksum']
        isMatch = False

        if (hash == generate_sha256(fp)):
            isMatch = True

        ret.append({
            'file_path': file_details['file_path'],
            'isMatch': isMatch
            })

    return ret


def create_hashes(file_list):
    """
    Creates sha256 checksums of every file in the list passed in.
    Expecting a list of file paths that can be opened for reading.
    """
    files_and_hashes = [];

    for file_path in file_list:
        files_and_hashes.append({
            'file_path': file_path,
            'checksum': generate_sha256(file_path)
            })

    return files_and_hashes


if __name__ == "__main__" : 
    """
    This subroutine generates a new manifest object for the 2 scripts that need to be 
    extracted from the .sublime-package file.

    This is meant to be run from within the CSSLint folder, top level.

    To run in Sublime, just hit cmd + b to build and check the console.

    Otherwise, you can run it in a terminal via `python version_file_checker.py`

    Place the result into CSSLint.py as the variable `manifest` (you'll see it in CSSLint.py)
    """

    print("===Creating CSSLint file manifest.===")
    print("Copy this into CSSLint.py if any of your scripts have changed.")
    pprint(create_hashes(FILE_LIST), indent=4)
