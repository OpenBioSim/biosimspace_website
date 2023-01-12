import sys
import os
import pygit2
import subprocess
import shlex

import BioSimSpace as project

project_dir = sys.argv[1]

repo = pygit2.Repository(project_dir)

branch = repo.head.shorthand
release = project.__version__
version = project.__version__.split("+")[0]

if version.find("untagged") != -1:
    print("This is an untagged branch")
    version = project.__manual_version__

print(f"Build docs for branch {branch} version {version}")

# we will only build docs for the main and devel branches
# (as these are moved into special locations)
is_tagged_release = False

try:
    force_build_docs = os.environ["FORCE_BUILD_DOCS"]
except Exception:
    force_build_docs = False

if branch not in ["main", "devel"]:
    if branch.find(version) != -1:
        print(f"Building the docs for tag {version}")
        is_tagged_release = True
    elif force_build_docs:
        print(f"Force-building docs for branch {branch}")
    else:
        print(f"We don't build the docs for branch {branch}")
        sys.exit(0)

os.environ["PROJECT_VERSION"] = version
os.environ["PROJECT_BRANCH"] = branch
os.environ["PROJECT_RELEASE"] = release


def run_command(cmd, dry=False):
    """Run the passed shell command"""
    if dry:
        print(f"[DRY-RUN] {cmd}")
        return

    print(f"[EXECUTE] {cmd}")

    try:
        args = shlex.split(cmd)
        subprocess.run(args).check_returncode()
    except Exception as e:
        print(f"[IGNORE ERROR] {e}")
        sys.exit(0)


os.chdir("gh-pages")

run_command("git config --local user.email 'action@github.com'")
run_command("git config --local user.name 'GitHub Action'")
run_command("git add .")
run_command("git commit -a -m 'Update website.'")
