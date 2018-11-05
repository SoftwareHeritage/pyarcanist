pyarcanist
==========

A simple cli tool for Phabricator. Aims at being some sort of arcanist on
steroids.

## Installation

Preferably in a venv:

```
(venv) user@host:~/src/project$ pip install pyarcanist
```

## Usage

The main cli entry point is the `pyarc` command:

```
(venv) user@host:~/src/project$ pyarc --help
Usage: pyarc [OPTIONS] COMMAND [ARGS]...

  Entry point

Options:
  -v, --verbose / --no-verbose
  -h, --host TEXT
  -t, --token TEXT
  --help                        Show this message and exit.

Commands:
  diff          List Diffs
  send-message  Send a harbormaster message
  whoami        Gives informations on the current user
```

By default, it will use your `~/.arcrc` file to get your Phabricator connection
credentials, but you can also pass the `--host` or `--token` options.

### Diff

This commands allows to query currently open Phabricator Diff objects (not only
your Diff).

```
(venv) user@host:~/src/project$ pyarc diff --help
Usage: pyarc diff [OPTIONS]

  List Diffs

Options:
  -u, --mine / --all-users
  -A, --all-repos / --current-repo
  -s, --summary / --default
  --help                          Show this message and exit.
```

If it is executed from a directory which is a git repo corresponding to a
Phabricator repository (a Diffusion oject), then the default behavior of the
`diff` command is to display Diff objects for the current repo only
(ie. `--current-repo`).

If it is executed in a directory that does not match any project in
Phabricator, then all (open) Diff are returned by default (ie. `--all-repos`).

Note that the matching between the local git repository and the Phabricator
Diffusion object if made on tracked remote repositories (git remote): it looks
for a configured tracked repositories of the local git which URL corresponds to
a public URI of one of the Phabricator Diffusion object.

Examples:

```
(venv) user@host:~/src/project$ pyarc diff -As
Changes Planned  D617: Always output valid JSON-LD.
Accepted         D619: Translate authors from package.json

(venv) user@host:~/src/project$ pyarc diff -A
Needs Review     D617
Repo: swh-indexer (DCIDX)
Author: vlorentz
Created: 7 days ago
Modified: 38 minutes ago
Summary:
  Always output valid JSON-LD.

  Our metadata extraction used to export a nested dict structure
  loosely based on JSON-LD with schema.org/CodeMeta.

  This diff makes it output proper JSON-LD data.

  Note that because of some issues (eg.
  https://github.com/codemeta/codemeta/issues/198 and the impossibility to
  represent a software entity without a specific version), I removed
  `softwareRequirements` and `softwareSuggestions` from the output

  As a side-effect, it resolves T1289

  PS: Morane, don't review this diff today, it can wait until tomorrow :)

Needs Review     D619
Repo: swh-indexer (DCIDX)
Author: vlorentz
Created: 6 days ago
Modified: 33 minutes ago
Summary:
  Translate authors from package.json

  This is an example of hardcoded translation that's impossible
  to do directly from the crosswalk table

```
