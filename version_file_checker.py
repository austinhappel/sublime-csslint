import os
from types import DictType
from hashlib import sha256
from pprint import pprint

def generate_sha256(file_path, block_size=1024):
    """Generates a sha256 checksum of the file passed in."""

    f = open(file_path)
    hash = sha256()

    if os.path.exists(file_path):
        while True:
            data = f.read(block_size)
            if not data:
                break
            
            hash.update(data)

        return hash.hexdigest()
    else:
        return False

    
def check_file_match(file_list, path_prefix):
    """
    Takes an array of file path/checksum objects and verifies that 
    the checksum matches the file in the target_dir.
    """
    ret = []

    for file_details in file_list:
        fp = file_details['file_path']
        hash = file_details['checksum']
        isMatch = False

        if (hash == generate_sha256(fp)):
            isMatch = True

        ret.append({
            'file_path': fp,
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
    """

    file_list = [
        os.path.join('scripts/csslint/csslint-rhino.js'),
        os.path.join('scripts/rhino/js.jar'),
    ]

    print("===Creating CSSLint file manifest.===")
    print("Copy this into CSSLint.py if any of your scripts have changed.")
    pprint(create_hashes(file_list), indent=4)
