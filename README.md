# password-manager

Cross platform offline gui and tui password manager.
Crypto stuff done with [pycryptodome][1].
GUI done with [pyside6][2].
TUI done with [textualize][3].

> [!WARNING]
> This is a personal project that intends to manage sensitive data. Just because its open source it doesn't mean its safe. Read trough the source code and build from source. I will provide binaries, these binaries will only ever be found in this repo.

## Goal

I was using Bitwarden for some time, but my anxiety came over me and i made my own password manager. Bitwarden might be open source, but its a lot of code to read trough. Even if you read trough all of it, whos to say that they dont run a backdoored fork?

## Features

Its very limited in its nature to keep the codebase as compact as possible in case you want to fully read trough it. However it does have some nice features:
 - Cross Platform (linux, windows, mac)
 - GUI and CLI
 - Generate random passwords
 - what can it store?:
   - name (website, service, etc...)
   - username
   - email
   - password
   - extra info (like a notes field)
   - creation date
   - last edit date
   - uuid (internal putposes only)

## Usage

The simplest way is to just [download the binaries][6]. However downloading and running binaries is always risky, i encourage to clone/fork the repo and build from source:

Prerequisites:
 - [astral uv][4]

<details><summary>Just run without making binaries</summary>

- clone repo:
  ```bash
  git clone https://github.com/p1geondove/password-manager
  ```
- cd into repo:
  ```bash
  cd password-manager
  ```
- create venv and add packages:
  ```bash
  uv sync
  ```
- run the software:
  ```bash
  uv run main.py
  ```

</details>

<details>
<summary>Build binaries from source</summary>

1. clone repo:
   ```bash
   git clone https://github.com/p1geondove/password-manager
   ```
2. cd into repo:
   ```bash
   cd password-manager
   ```
3. create venv and add packages:
   ```bash
   uv sync
   ```
4. make binary:
   - **Linux**:
     ```bash
     ./build.sh
     ```
   - **Windows**:
     1. [read through this][5]
     2. open PowerShell as admin
     3. run:
        ```powershell
        Set-ExecutionPolicy unrestricted
        ```
     4. return to the shell with the password-manager
     5. run:
        ```powershell
        ./build.ps1
        ```
</details>


## Technical details

### File layout

<details><summary>General encrypted file</summary>

  Every file has 5 segments that can be split up like this:
  - Bytes 0-32: salt
  - Bytes 32-48: nonce
  - Bytes 48-64: mac tag for verification
  - Byte 64: content type -> 0=bytes 1=string 2=json
  - Bytes 65-: ciphertext

</details>
<details><summary>Password manager file</summary>

  A password data containing file is in essence just json. The python type actually used is a `dict[UUID, PWField]`.
  A UUID in this case is just a python builtin uuid.uuid4() like `e18d1093-fcdb-468b-9e5a-6b4a4b9aff22` for example.
  A PWField is a dataclass containting the uuid again as well as username, email, password, extra info, creation date and last edit date.
  The uuids are internally used as UUID types, but get saved as string, in python parsing uuids like this is as simple as using `uuid.UUID(xyz)` while converting to string is done via `str(xyz)`.
  Times are format `%Y-%m-%d %H:%M:%S.%f` which should be normal iso format, ex: `2026-06-18 23:31:29.104373`, to parse the you can use `datetime.fromisoformat(xyz)`, string conversion is done via `str(xyz)`.

</details>

### en-/decryption

<details><summary>Click to expand</summary>

  The files get encrypted using AES, 256 bits. All of the crypto stuff is done via [pycryptodome][1].
  For that a key is derived from a password and a random 256 bit salt using PBKDF2 using 1 million iterations on SHA512. 1 million iterations of SHA512 somewhat time consuming, but thats a good thing since it makes brute force extremely time consuming. Ill test the speed of that on a very low power machine as well, but as long as the login takes less then a second i think its fine and doesnt break user experience. This is only really done once tho, since after that the key and salt are stored in ram. This has the benefit of instantly updating changes to the password file while also preventing malicious actors to steal your actual password. (Altho i guess if someone has that level of access to your machine they could just install a keylogger)
  This program also creates a pepper that is locally saved, where exactly is dependant on the operating system. The pepper file itself is not encrypted and can technically be easily read and stolen by malicious actors. However it does add another layer of security to the whole project. **The pepper is important for accessing your password file, if you loose it you wont be able to recover your passwords or encrypted files**
  There are multiple abstraction layers in `crypt.py`, such as basic methods for en-/decryption, file interfacing and password-file interface.

</details>

## AI

Of course i use AI to help me out. That does not mean that this is vibe-coded. Since im using this as my daily (well techincally monthly, since cookies and so forth) driver i want this to be as secure as possible. My stance on LLMs is not all to controversial i think, but i know what they can and cant do. **There is not a single line of code in this project that has been vibe-coded or copy pasted from any LLM**. So how do i use LLMs then? They are useful for telling me about what libraries there are, for example in this project a LLM told me about the existance of the external [`appdirs`][7] library. LLMs are helpful for formatting `.md` files, they helped me find out about the existence of the `> Warning` block that you see at the top. Also im not all too familiar with textualize, so LLMs really can help out on the frontend

[1]: https://pycryptodome.readthedocs.io/en/latest/src/introduction.html
[2]: https://doc.qt.io/qtforpython-6/index.html
[3]: https://www.textualize.io/
[4]: https://docs.astral.sh/uv/getting-started/installation/
[5]: https://superuser.com/questions/106360/how-to-enable-execution-of-powershell-scripts
[6]: https://github.com/p1geondove/password-manager/releases
[7]: https://pypi.org/project/appdirs/

