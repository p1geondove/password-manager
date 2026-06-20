import json
from pathlib import Path
from uuid import uuid4, UUID
from datetime import datetime

from Crypto.Cipher import AES
from Crypto.Hash import SHA512
from Crypto.Random import get_random_bytes
from Crypto.Protocol.KDF import PBKDF2

from .const import *
from .helper import timer

class DecryptError(Exception):
    pass

class ContentTypeError(Exception):
    pass

class MissingKeyError(Exception):
    pass

def get_pepper():
    """ returns local stored pepper or creates new one if none is set """
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
            raise ContentTypeError(f"illegal content_type specifier {content_type}")
        return obj

    def parse_raw(self):
        """
        parses a encrypted file to tuple
        0 -> salt:bytes
        1 -> nonce:bytes
        2 -> mactag:bytes
        3 -> content_type:int
        4 -> ciphertext:bytes
        """
        raw = self.file_path.read_bytes()
        salt = raw[self.off_salt:self.off_nonce]
        nonce = raw[self.off_nonce:self.off_mactag]
        mactag = raw[self.off_mactag:self.off_content_type]
        content_type = raw[self.off_content_type]
        ciphertext = raw[self.off_ciphertext:]
        return salt, nonce, mactag, content_type, ciphertext

    def load(self):
        """
        loads contents of a file using the set key and salt
        raises MissingKeyError if key and salt has not been set yet
        raises DecryptError if MAC check failed
        """
        if self.key is None or self.salt is None:
            raise MissingKeyError("missing key and salt, use Cryptor.edit_password first to get key and salt")
        _, nonce, mactag, content_type , ciphertext = self.parse_raw()
        try:
            plaintext = decrypt(ciphertext, self.key, nonce, mactag)
        except ValueError:
            raise DecryptError("Cant decrypt contents, wrong password, wrong pepper or corrupted data")
        if content_type == 0: # parse plaintext to bytes -> nothing changes
            pass
        elif content_type == 1: # decode plaintext to str
            plaintext = plaintext.decode()
        elif content_type == 2: # decode plaintext to json / dict
            plaintext = json.loads(plaintext)
        return plaintext

    def load_from_password(self, password:str):
        """ uses Cryptor.edit_password to get salt and key, then calls Cryptor.load """
        self.edit_password(password)
        return self.load()

    def save(self, obj):
        """
        formats obj to bytes according to its type
        obj:bytes -> obj stays as bytes
        obj:str -> obj gets utf8 encoded to bytes
        obj:dict -> obj gets converted to json and then dumped
        raises MissingKeyError if no key and salt has been set -> use Cryptor.edit_password first
        raises NotImplementedError if illegal obj type has been passed
        """

        if self.key is None or self.salt is None:
            raise MissingKeyError("missing key and salt, use Cryptor.edit_password first to get key and salt")
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
        """ same as Cryptor.save, just calls Cryptor.edit_password first """
        self.edit_password(password)
        self.save(obj)

    def edit_password(self, password:str):
        """ checks wether the encrypted file exists and pulls the salt from that, otherwise generates new key/salt pair from password """
        if self.file_path.exists():
            salt = self.parse_raw()[0]
            self.key, self.salt = get_key(password, salt)
        else:
            self.key, self.salt = get_key(password)


from dataclasses import dataclass

@dataclass()
class PWField():
    """ A so called Field or Entry for the password manager/file that can store several bits of data """
    uuid:UUID
    name:str
    username:str
    email:str
    password:str
    extra:str
    creation_time:datetime
    edit_time:datetime

    @classmethod
    def from_json_entry(cls, json_obj:tuple[str,str,str,str,str,str,str,str]):
        """ returns a new PWField from a password file entry """
        uuid = UUID(json_obj[0])
        createion_time = datetime.fromisoformat(json_obj[6])
        edit_time = datetime.fromisoformat(json_obj[7])
        return cls(uuid, *json_obj[1:6], createion_time, edit_time)

    @classmethod
    def dict_from_json(cls, json_obj):
        """ returns a dict[UUID, PWField] parsed from a password file """
        return {UUID(key):cls.from_json_entry(vals) for key,vals in json.loads(json_obj).items()}

    def to_tuple(self) -> tuple[str,str,str,str,str,str,str,str]:
        """ returns itself as a tuple """
        return str(self.uuid), self.name, self.username, self.email, self.password, self.extra, str(self.creation_time), str(self.edit_time)

    def to_json_friendly(self) -> dict[str, tuple[str,str,str,str,str,str,str,str]]:
        return {str(self.uuid): self.to_tuple()}

class PWManager:
    def __init__(self, password:str):
        self.cryptor = Cryptor()
        self.cryptor.edit_password(password)
        if not PATH_PASSWORD_FILE.exists():
            self.save_to_file({})
        else:
            self.cryptor.load_from_password(password)

    def load_from_file(self):
        return PWField.dict_from_json(self.cryptor.load())

    def save_to_file(self, password_data:dict[UUID, PWField]):
        json_dict = {}
        for uuid, pwfield in password_data.items():
            json_dict[str(uuid)] = pwfield.to_tuple()
        self.cryptor.save(json.dumps(json_dict))

    def add_entry(self, name:str="", username:str="", email:str="", password:str="", extra:str=""):
        password_data = self.load_from_file()
        uuid = uuid4()
        while uuid in password_data:
            uuid = uuid4()
        new_entry = PWField(uuid, name, username, email, password, extra, datetime.now(), datetime.now())
        password_data[uuid] = new_entry
        self.save_to_file(password_data)
        return new_entry

    def remove_entry(self, uuid:UUID):
        password_data = self.load_from_file()
        if not uuid in password_data: return
        del password_data[uuid]
        self.save_to_file(password_data)

    def update_entry(self, uuid:UUID, name:str|None=None, username:str|None=None, email:str|None=None, password:str|None=None, extra:str|None=None):
        password_data = self.load_from_file()
        if uuid in password_data:
            field = password_data[uuid]
            field.name = name if name else field.name
            field.username = username if username else field.username
            field.email = email if email else field.email
            field.password = password if password else field.password
            field.extra = extra if extra else field.extra
            field.edit_time = datetime.now()
        else:
            field = PWField(
                uuid,
                name if name else "",
                username if username else "",
                email if email else "",
                password if password else "",
                extra if extra else "",
                datetime.now(),
                datetime.now()
            )
            password_data[uuid] = field
        self.save_to_file(password_data)

    def get_entry(self, uuid:UUID):
        return self.load_from_file()[uuid]

