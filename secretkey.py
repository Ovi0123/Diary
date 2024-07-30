from cryptography.fernet import Fernet

# Generate a key and write it to a file
def generate_key():
    key = Fernet.generate_key()
    with open("secret.key", "wb") as key_file:
        key_file.write(key)

# Uncomment the next line and run this script once to generate the key
generate_key()
