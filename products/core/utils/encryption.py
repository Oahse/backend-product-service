from argon2 import PasswordHasher
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.backends import default_backend
from os import urandom

class PasswordManager:
    def __init__(self):
        # Initialize Argon2 PasswordHasher
        self.ph = PasswordHasher()

    # Hashing a password
    def hash_password(self, password: str) -> str:
        return self.ph.hash(password)

    # Verifying a password
    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        try:
            # Verify the hashed password against the input password
            self.ph.verify(hashed_password, plain_password)
            return True
        except Exception as e:
            # Return False if an error occurs (e.g., password doesn't match)
            return False


# Example usage
# password_manager = PasswordManager()

# # Hash a password
# password = "user_password"
# hashed_password = password_manager.hash_password(password)
# print("Hashed Password:", hashed_password)

# # Verifying the password
# is_correct = password_manager.verify_password(password, hashed_password)
# print("Password Verified:", is_correct)

# # Trying to verify with a wrong password
# is_correct_wrong = password_manager.verify_password("wrong_password", hashed_password)
# print("Password Verified (with wrong password):", is_correct_wrong)


class AESHandler:
    def __init__(self, key: bytes = None):
        """Initialize the AESHandler class. Optionally, provide a 256-bit key."""
        if key:
            if len(key) != 32:  # AES-256 requires 32 bytes (256 bits) key
                raise ValueError("Key must be 32 bytes for AES-256 encryption.")
            self.key = key
        else:
            # If no key is provided, generate a random 32-byte key (AES-256)
            raise ValueError("Provide your key. Key must be 32 bytes for AES-256 encryption.")

    def encrypt_data(self, data: bytes):
        """Encrypt the data using AES encryption with a random IV."""
        iv = urandom(16)  # Initialization Vector (16 bytes for AES)
        cipher = Cipher(algorithms.AES(self.key), modes.CBC(iv), backend=default_backend())
        encryptor = cipher.encryptor()

        # Pad the data to be a multiple of block size (16 bytes for AES)
        padding_length = 16 - (len(data) % 16)
        padded_data = data + bytes([padding_length]) * padding_length

        encrypted_data = encryptor.update(padded_data) + encryptor.finalize()
        
        # Prepend IV to the encrypted data so we can use it for decryption later
        return iv + encrypted_data

    def decrypt_data(self, encrypted_data: bytes):
        """Decrypt the data using AES encryption."""
        iv = encrypted_data[:16]  # The first 16 bytes are the IV
        cipher = Cipher(algorithms.AES(self.key), modes.CBC(iv), backend=default_backend())
        decryptor = cipher.decryptor()

        # Decrypt the data
        decrypted_data = decryptor.update(encrypted_data[16:]) + decryptor.finalize()
        
        # Remove padding
        padding_length = decrypted_data[-1]
        return decrypted_data[:-padding_length]

# Example usage:
# if __name__ == "__main__":
    # # Generate or load a 256-bit AES key
    # aes_handler = AESHandler()

    # # Example data to encrypt
    # data = b"Hello, this is some secret data!"

    # # Encrypt data
    # encrypted_data = aes_handler.encrypt_data(data)
    # print(f"Encrypted Data: {encrypted_data}")

    # # Decrypt data
    # decrypted_data = aes_handler.decrypt_data(encrypted_data)
    # print(f"Decrypted Data: {decrypted_data.decode()}")
