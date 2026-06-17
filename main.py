import sys

from pathlib import Path

from Crypto.Cipher import AES
from Crypto.Hash import SHA512
from Crypto.Random import get_random_bytes
from Crypto.Protocol.KDF import PBKDF2

SIZE_SALT = 32
SIZE_PEPPER = 32
SIZE_KEY = 32
SIZE_NONCE = 16
SIZE_MAC = 16
PBKDF2_ITERS = 1_000_000

def get_pepper():
    """
    returns local stored pepper or creates new one if none is set
    """
    if sys.platform == "linux":
        pepper_path = Path.home() / ".config" / "password_manager" / "pepper"
        if not pepper_path.exists():
            print("making new pepper")
            pepper_path.parent.mkdir(parents=True, exist_ok=True)
            pepper = get_random_bytes(SIZE_PEPPER)
            pepper_path.write_bytes(pepper)
        else:
            pepper = pepper_path.read_bytes()
        return pepper
    else:
        raise NotImplementedError("only supported on linux")

def get_key(password:str, salt:bytes|None = None) -> tuple[bytes, bytes]:
    """
    generates key from password and salt
    creates new salt when none is passed
    returns key and salt
    """

    if salt is None:
        salt = get_random_bytes(SIZE_SALT)
    key = PBKDF2(password, salt + get_pepper(), dkLen=SIZE_KEY, count=PBKDF2_ITERS, hmac_hash_module=SHA512)
    return key, salt

def encrypt(plaintext:str|bytes, password:str) -> tuple[bytes, bytes, bytes, bytes]:
    """
    encrypts the plaintext from cleartext-password
    returns ciphertext, salt, nonce and mactag
    """
    if isinstance(plaintext, str):
        plaintext = plaintext.encode()
    key, salt = get_key(password)
    cipher = AES.new(key=key, mode=AES.MODE_GCM)
    ciphertext, mactag = cipher.encrypt_and_digest(plaintext)
    return ciphertext, salt, bytes(cipher.nonce), mactag

def decrypt(ciphertext:bytes, salt:bytes, nonce:bytes, mactag:bytes, password:str):
    """
    decrypts ciphertext and veryfies content
    returns plaintext or raises ValueError
    """
    key,_ = get_key(password, salt)
    print("DEC", key)
    cipher = AES.new(key=key, mode=AES.MODE_GCM, nonce=nonce)
    plaintext = cipher.decrypt_and_verify(ciphertext, mactag)
    return plaintext

def main():
    text = "Very secret text"
    password = "testpassword"
    ciphertext, salt, nonce, mactag = encrypt(text, password)
    print(f"ciphertext: {ciphertext} {len(ciphertext)}")
    print(f"salt: {salt} {len(salt)}")
    print(f"nonce: {nonce} {len(nonce)}")
    print(f"mactag: {mactag} {len(mactag)}")
    print()
    clear = decrypt(ciphertext, salt, nonce, mactag, password)
    print(clear)

if __name__ == "__main__":
    main()
