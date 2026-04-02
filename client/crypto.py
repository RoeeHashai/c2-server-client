# asymmetric encryption
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import padding
from cryptography.hazmat.primitives import hashes

# symmetric encryption
from cryptography.hazmat.primitives.ciphers.aead import AESCCM

from network.tcp import Tcp
import os

class Security:
    def __init__(self):
        self.__public_key = None
        self.__symmetric_key = None
        
    def handshake(self,conn):
        pk = Tcp.recive(conn)
        if not pk:
            raise Exception("No data received during handshake")
        self.__public_key = serialization.load_pem_public_key(pk, backend=default_backend())
        key = AESCCM.generate_key(bit_length=256)
        ciphertext_key = self.__public_key.encrypt(
            key,
            padding.OAEP(
                mgf=padding.MGF1(algorithm=hashes.SHA256()),
                algorithm=hashes.SHA256(),
                label=None
            )
        )
        Tcp.send(conn, ciphertext_key)
        self.__symmetric_key = AESCCM(key)
        
    def encrypt(self, plaintext):
        IV = os.urandom(13)
        ciphertext = self.__symmetric_key.encrypt(IV, plaintext.encode(), None)
        return IV + ciphertext
    
    def decrypt(self, ciphertext):
        IV = ciphertext[:13]
        plaintext = self.__symmetric_key.decrypt(IV, ciphertext[13:], None)
        return plaintext.decode()
 