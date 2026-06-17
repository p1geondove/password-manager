import json
from dataclasses import dataclass
from pathlib import Path

from Crypto.Cipher import AES
from Crypto.Hash import SHA512
from Crypto.Random import get_random_bytes
from Crypto.Protocol.KDF import PBKDF2

from .const import *

def get_pepper():
    """
    returns local stored pepper or creates new one if none is set
    """
    if not PATH_PEPPER.exists():
        PATH_PEPPER.parent.mkdir(parents=True, exist_ok=True)
        pepper = get_random_bytes(SIZE_PEPPER)
        PATH_PEPPER.write_bytes(pepper)
    else:
        pepper = PATH_PEPPER.read_bytes()
    return pepper

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

def encrypt(plaintext:bytes, key:bytes):
    """
    encrypts the plaintext from derived key
    returns ciphertext, nonce and mactag
    """
    cipher = AES.new(key=key, mode=AES.MODE_GCM)
    ciphertext, mactag = cipher.encrypt_and_digest(plaintext)
    return ciphertext, bytes(cipher.nonce), mactag

def encrypt_from_password(plaintext:bytes, password:str) -> tuple[bytes, bytes, bytes, bytes]:
    """
    encrypts the plaintext from cleartext-password
    returns ciphertext, salt, nonce and mactag
    """
    key, salt = get_key(password)
    ciphertext, nonce, mactag = encrypt(plaintext, key)
    return ciphertext, salt, nonce, mactag

def decrypt(ciphertext:bytes, key:bytes, nonce:bytes, mactag:bytes):
    """
    decrypts ciphertext and veryfies content from derived key
    returns plaintext or raises ValueError
    """
    cipher = AES.new(key=key, mode=AES.MODE_GCM, nonce=nonce)
    return cipher.decrypt_and_verify(ciphertext, mactag)

def decrypt_from_password(ciphertext:bytes, salt:bytes, nonce:bytes, mactag:bytes, password:str):
    """
    decrypts ciphertext and veryfies content from password
    returns plaintext or raises ValueError
    """
    key,_ = get_key(password, salt)
    return decrypt(ciphertext, key, nonce, mactag)

@dataclass
class EncFile:
    salt:bytes
    nonce:bytes
    mactag:bytes
    content_type:int
    ciphertext:bytes

class Cryptor:
    """
    Interfaces Files
    File Layout:
    Bytes 0-32: salt
    Bytes 32-48: nonce
    Bytes 48-64: mac tag
    Byte 64: content type -> 0=bytes 1=string 2=json
    Bytes 65-: ciphertext
    Actual offsets depend on various sizes set in const.py but i dont intend on changing these
    """

    off_salt = 0
    off_nonce = SIZE_KEY
    off_mactag = off_nonce + SIZE_NONCE
    off_content_type = off_mactag + SIZE_MAC
    off_ciphertext = off_content_type + 1

    def __init__(self, file_path:Path = PATH_PASSWORD_FILE) -> None:
        self.file_path = file_path
        self.key:bytes|None = None
        self.salt:bytes|None = None

    @staticmethod
    def encode(obj):
        """ encodes object to bytes and returns the content_type int with it """
        if isinstance(obj, bytes):
            content_type = int.to_bytes(0)
            plaintext = obj
        elif isinstance(obj, str):
            content_type = int.to_bytes(1)
            plaintext = obj.encode()
        elif isinstance(obj, dict):
            content_type = int.to_bytes(2)
            plaintext = json.dumps(obj).encode()
        else:
            raise NotImplementedError(f"no support for saving objects of type {type(obj)}")
        return plaintext, content_type

    @staticmethod
    def decode(payload:bytes, content_type:int):
        """ decodes bytes to specified content type. Might raise ValueError if illegal content_type specifier is passed """
        if content_type == 0: # parse plaintext to bytes -> nothing changes
            obj = payload
        elif content_type == 1: # decode plaintext to str
            obj = payload.decode()
        elif content_type == 2: # decode plaintext to json / dict
            obj = json.loads(payload)
        else:
            raise ValueError(f"illegal content_type specifier {content_type}")
        return obj

    def parse_raw(self):
        raw = self.file_path.read_bytes()
        salt = raw[self.off_salt:self.off_nonce]
        nonce = raw[self.off_nonce:self.off_mactag]
        mactag = raw[self.off_mactag:self.off_content_type]
        content_type = raw[self.off_content_type]
        ciphertext = raw[self.off_ciphertext:]
        return salt, nonce, mactag, content_type, ciphertext

    def load(self):
        if self.key is None or self.salt is None:
            raise ValueError("missing key and salt, use Cryptor.open_from_password first to get key and salt")
        _, nonce, mactag, content_type , ciphertext = self.parse_raw()
        plaintext = decrypt(ciphertext, self.key, nonce, mactag)
        if content_type == 0: # parse plaintext to bytes -> nothing changes
            pass
        elif content_type == 1: # decode plaintext to str
            plaintext = plaintext.decode()
        elif content_type == 2: # decode plaintext to json / dict
            plaintext = json.loads(plaintext)
        return plaintext

    def load_from_password(self, password:str):
        salt = self.parse_raw()[0]
        self.key, self.salt = get_key(password, salt)
        return self.load()

    def save(self, obj):
        if self.key is None or self.salt is None:
            raise ValueError("missing key and salt, use Cryptor.open_from_password first to get key and salt")
        if isinstance(obj, bytes):
            content_type = int.to_bytes(0)
            plaintext = obj
        elif isinstance(obj, str):
            content_type = int.to_bytes(1)
            plaintext = obj.encode()
        elif isinstance(obj, dict):
            content_type = int.to_bytes(2)
            plaintext = json.dumps(obj).encode()
        else:
            raise NotImplementedError(f"no support for saving objects of type {type(obj)}")
        ciphertext, nonce, mactag = encrypt(plaintext, self.key)
        payload = self.salt + nonce + mactag + content_type + ciphertext
        self.file_path.write_bytes(payload)

    def save_from_password(self, obj, password:str):
        self.key, self.salt = get_key(password)
        self.save(obj)

