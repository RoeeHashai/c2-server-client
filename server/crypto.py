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
import logging

class Security:
    def __init__(self):
        self.__private_key = rsa.generate_private_key(
            public_exponent=65537,
            key_size=2048,
            backend=default_backend()
        )
        self.__public_key = self.__private_key.public_key()
        self.__symmetric_keys = {} # { client_id : symmetric_key }
        
    def get_public_key(self):
        return self.__public_key.public_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PublicFormat.SubjectPublicKeyInfo
        )
        
    def handshake(self, cid, conn):
        # send the pk
        Tcp.send(conn, self.get_public_key())
        # get symmetric key from client
        ciphertext_key = Tcp.recive(conn)
        if not ciphertext_key:
            raise Exception("No data received during handshake")
        key = self.__private_key.decrypt(
            ciphertext_key,
            padding.OAEP(
                mgf=padding.MGF1(algorithm=hashes.SHA256()),
                algorithm=hashes.SHA256(),
                label=None
            )
        )
        self.__symmetric_keys[cid] = AESCCM(key)
        
    def encrypt(self, cid, plaintext):
        if cid in self.__symmetric_keys:
            IV = os.urandom(13)
            symmetic_key = self.__symmetric_keys[cid]
            ciphertext = symmetic_key.encrypt(IV, plaintext.encode(), None)
            return IV + ciphertext
        
    def decrypt(self, cid, ciphertext):
        if cid in self.__symmetric_keys:
            IV = ciphertext[:13]
            symmetic_key = self.__symmetric_keys[cid]
            plaintext = symmetic_key.decrypt(IV, ciphertext[13:], None)
            return plaintext.decode()
        
    def remove_client(self, cid):
        logging.info(f"Removing client {cid} from security manager")
        self.__symmetric_keys.pop(cid, None)
