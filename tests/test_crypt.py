from password_manager import crypt, const

PASSWORD = "\"a\\0ß~-"
SALT = b"0"*const.SIZE_SALT
PAYLOAD_STR = "Very important and sensitive data"
PAYLOAD_BIN = PAYLOAD_STR.encode()
PAYLOAD_OBJ = {"who":("keeps","shitting"),"my":("pants","?")}

def test_keygen_nosalt():
    key, salt = crypt.get_key(PASSWORD)
    assert isinstance(key, bytes)
    assert isinstance(salt, bytes)
    assert len(key) == const.SIZE_KEY
    assert len(salt) == const.SIZE_SALT

def test_keygen_salt():
    key, salt = crypt.get_key(PASSWORD, SALT)
    assert salt == SALT

def test_crypt_nopw():
    key, salt = crypt.get_key(PASSWORD)
    ciphertext, nonce, mactag = crypt.encrypt(PAYLOAD_BIN, key)
    clear = crypt.decrypt(ciphertext, key, nonce, mactag)
    assert clear == PAYLOAD_BIN

def test_crypt_pw():
    ciphertext, salt, nonce, mactag = crypt.encrypt_from_password(PAYLOAD_BIN, PASSWORD)
    clear = crypt.decrypt_from_password(ciphertext, salt, nonce, mactag, PASSWORD)
    assert clear == PAYLOAD_BIN

def test_cryptor_nopw():
    c = crypt.Cryptor()
    key, salt = crypt.get_key(PASSWORD)
    c.salt = salt
    c.key = key
    c.save(PAYLOAD_BIN)
    clear = c.load()
    assert isinstance(clear, type(PAYLOAD_BIN))
    assert clear == PAYLOAD_BIN

def test_cryptor_pw():
    c = crypt.Cryptor()
    c.save_from_password(PAYLOAD_STR, PASSWORD)
    clear = c.load_from_password(PASSWORD)
    assert isinstance(clear, type(PAYLOAD_STR))
    assert clear == PAYLOAD_STR
