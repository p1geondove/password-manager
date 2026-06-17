from pathlib import Path

from appdirs import user_state_dir, user_data_dir

SIZE_SALT = 32
SIZE_PEPPER = 32
SIZE_KEY = 32
SIZE_NONCE = 16
SIZE_MAC = 16
PBKDF2_ITERS = 1_000_000

PATH_STATEDIR = Path(user_state_dir("password_manager"))
PATH_STATEDIR.mkdir(parents=True, exist_ok=True)
PATH_PEPPER = PATH_STATEDIR / "pepper"

PATH_PASSWORD_FILE = Path(user_data_dir("password_manager")) / "vault.enc"
PATH_PASSWORD_FILE.parent.mkdir(parents=True, exist_ok=True)
