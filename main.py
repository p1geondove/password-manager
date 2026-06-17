from password_manager import crypt

def main():
    
    text = "Very secret text"
    password = "testpassword"
    
    print("testing crypt base enc-dec")
    key, salt = crypt.get_key(password)
    ciphertext, nonce, mactag = crypt.encrypt(text.encode(), key)
    clear = crypt.decrypt(ciphertext, key, nonce, mactag)
    print(clear)

    print("\ntesting crypt base enc-dec password version")
    ciphertext, salt, nonce, mactag = crypt.encrypt_from_password(text.encode(), password)
    print(f"ciphertext: {ciphertext} {len(ciphertext)}")
    print(f"salt: {salt} {len(salt)}")
    print(f"nonce: {nonce} {len(nonce)}")
    print(f"mactag: {mactag} {len(mactag)}")
    clear = crypt.decrypt_from_password(ciphertext, salt, nonce, mactag, password)
    print(clear)

    print("\ntesting Cryptor")
    c = crypt.Cryptor()
    print(f"Cryptor file path: {c.file_path}")
    c.save_from_password(text, password)
    clear = c.open_from_password(password)
    print(clear)
    text = b"sensitive binary"
    c.save(text)
    clear = c.open()
    print(clear)
    obj = {"website1":("username1","password1"), "website2":("username2", "password2")}
    c.save(obj)
    obj = c.open()
    print(obj)

if __name__ == "__main__":
    main()
