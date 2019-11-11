import os
import rsa
import uuid
import base64
import logging
from Crypto import Random
from Crypto.Cipher import AES
from Crypto.Hash import SHA256


def default_device_serial():
    nic_mac = str(hex(uuid.getnode()))
    serial = bytes(nic_mac, 'utf-8')
    return serial


def sha256_digest(content):
    return base64.b64encode(SHA256.new(content).digest())


def sha256_recover(content, pvt_path):
    ret = _decrypt_by_private(base64.b64decode(content), pvt_path)
    return SHA256.new(ret).digest()


def _generate_rsa_pair(keysize=1024):
    (pubkey, pvtkey) = rsa.newkeys(keysize)
    with open('public.pem', 'wb') as pubf, open('private.pem', 'wb') as pvtf:
        pubf.write(pubkey.save_pkcs1())
        pvtf.write(pvtkey.save_pkcs1())
    logging.debug(">>> generated key pairs")


def _encrypt_by_public(key, pub_file_path):
    with open(pub_file_path, 'r') as pf:
        return rsa.encrypt(key, rsa.PublicKey.load_pkcs1(pf.read()))


def _decrypt_by_private(key, pvt_file_path):
    with open(pvt_file_path, 'r') as pf:
        return rsa.decrypt(key, rsa.PrivateKey.load_pkcs1(pf.read()))


def _encrypt(sandbox_key, src_file, dest_file):
    IV = Random.new().read(AES.block_size)
    encryptor = AES.new(sandbox_key, AES.MODE_CBC, IV)
    with open(src_file, 'rb') as src, open(dest_file, 'wb') as dest:
        chunk_size = 64*1024
        file_size = str(os.path.getsize(src_file)).zfill(16)
        dest.write(bytes(file_size, 'utf-8'))
        dest.write(IV)
        while True:
            chunk = src.read(chunk_size)
            if len(chunk) == 0:
                break
            elif len(chunk) % 16 != 0:
                chunk += bytes(' ', 'utf-8')*(16 - len(chunk)%16)
            dest.write(encryptor.encrypt(chunk))

def _decrypt(sandbox_key, src_file, dest_file):
    with open(src_file, 'rb') as src, open(dest_file, 'wb') as dest:
        chunk_size = 64*1024
        file_size = int(src.read(16))
        decryptor = AES.new(sandbox_key, AES.MODE_CBC, IV=src.read(16))
        while True:
            chunk = src.read(chunk_size)
            if len(chunk)==0:
                break
            dest.write(decryptor.decrypt(chunk))
        dest.truncate(file_size)

# TODO: these functions need to be tested before use it
def _sign_by_private(key, pvt_file_path):
    with open(pvt_file_path, 'r') as pf:
        return rsa.sign(key, rsa.PrivateKey.load_pkcs1(pf.read()), 'SHA-1')

def _verify_by_public(signature, pub_file_path, verify):
    with open(pub_file_path, 'r') as pf:
        return rsa.verify(verify, signature, rsa.PublicKey.load_pkcs1(pf.read()))

