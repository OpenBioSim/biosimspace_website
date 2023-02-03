# deduplicate the website by finding all unique files and
# replacing duplicates with symbolic links

from hashlib import md5

import pygit2
import os
import sys
import BioSimSpace as project

project_dir = sys.argv[1]

repo = pygit2.Repository(project_dir)

branch = repo.head.shorthand

branch = project.__branch__
release = project.__version__
version = project.__version__.split("+")[0]

if version.find("untagged") != -1:
    print("This is an untagged branch")
    version = project.__manual_version__

print(f"Build docs for branch {branch} version {version}")

# we will only build docs for the main and devel branches
# (as these are moved into special locations)
is_tagged_release = False

os.environ["PROJECT_VERSION"] = version
os.environ["PROJECT_BRANCH"] = branch
os.environ["PROJECT_RELEASE"] = release

files = {}

digests = {}

duplicates = []

# calculate the md5 digest of all files
for root, dirs, files in os.walk("gh-pages", onerror=None, followlinks=False):
    if root.find(".git") != -1:
        continue

    for filename in files:
        if filename.startswith("."):
            continue

        fullpath = os.path.join(root, filename)

        if os.path.isfile(fullpath):
            # really don't follow links
            if os.path.islink(fullpath):
                print(f"Skipping {fullpath} as link")
                continue

            with open(fullpath, "rb") as FILE:
                data = FILE.read()

            # only care about files that are larger than 32K
            if len(data) < 32 * 1024:
                continue

            # md5 plus filesize should be unique enough
            hsh = md5(data)
            digest = f"{hsh.hexdigest()}-{len(data)}"

            if digest in digests:
                digests[digest].append(fullpath)
                duplicates.append(digest)
                print(f"Duplicate large file {fullpath}")
            else:
                digests[digest] = [fullpath]
        else:
            print(f"is dir? {fullpath}")

current_dir = os.getcwd()

if len(duplicates) == 0:
    print("There are no depulicates to de-dup")

for duplicate in duplicates:
    # the duplicate with the shortest path name is the one we want
    # to keep
    files = digests[duplicate]

    common_prefix = os.path.commonprefix(files)

    best_file = files[0]

    for file in files[1:]:
        if len(file) < len(best_file):
            best_file = file

    files.remove(best_file)

    for file in files:
        base = os.path.dirname(file)
        name = os.path.basename(file)
        relative = os.path.relpath(best_file, os.path.dirname(file))

        print(f"Change dir to {base}")
        os.chdir(base)

        if not os.path.exists(name):
            print(f"Weird - missing name? {name}")
            print(f"Returning to {current_dir}")
            os.chdir(current_dir)
            continue

        if not os.path.exists(relative):
            print(f"Weird - missing relative? {relative}")
            print(f"Returning to {current_dir}")
            os.chdir(current_dir)
            continue

        print(f"Linking from {best_file} => {file}")

        # remove the duplicate
        print(f"Remove {name}")
        os.unlink(name)

        # create a symlink
        print(f"link {relative} => {name}")
        os.symlink(relative, name)

        print(f"Returning to {current_dir}")
        os.chdir(current_dir)
