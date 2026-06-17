# password-manager
Cross platform offline gui and tui password manager.
Crypto stuff done with [pycryptodome][1].
GUI done with [pyside6][2].
TUI done with [textualize][3].

# WARRENTY
This is a personal project that intends to manage sensitive data. Just because its open source it doesn't mean its safe. Read trough the source code and build from source. I will provide binaries, these binaries will only ever be found in this repo.

# Goal
I was using Bitwarden for some time, but my anxiety came over me and i made my own password manager. Bitwarden might be open source, but its a lot of code to read trough. Even if you read trough all of it, whos to say that they dont run a backdoored fork?

# Features
Its very limited in its nature to keep the codebase as compact as possible in case you want to fully read trough it. However it does have some nice features:
 - Cross Platform (linux, windows, mac)
 - GUI and CLI
 - Generate random passwords
 -

# Usage
The simplest way is to just download the binaries. However downloading and running binaries is always risky, i encourage to clone/fork the repo and build from source:

Prerequisites:
 - python (duh...)
 - [astral uv][4]

Build binaries from source:
 - clone repo: `git clone https://github.com/p1geondove/password-manager`
 - cd into repo: `cd password-manager`
 - create venv and add packages: `uv sync`
 - make binary:
   - linux: `./build.sh`
   - windows:
     - [read trough this][5]
     - open powershell as admin
     - `Set-ExecutionPolicy unrestricted`
     - back to shell with the password-manager
     - `./build.ps1`

Just run without making binaries:
 - clone repo: `git clone https://github.com/p1geondove/password-manager`
 - cd into repo: `cd password-manager`
 - create venv and add packages: `uv sync`
 - run the software: `uv run main.py`

[1]: https://pycryptodome.readthedocs.io/en/latest/src/introduction.html
[2]: https://doc.qt.io/qtforpython-6/index.html
[3]: https://www.textualize.io/
[4]: https://docs.astral.sh/uv/getting-started/installation/
[5]: https://superuser.com/questions/106360/how-to-enable-execution-of-powershell-scripts
