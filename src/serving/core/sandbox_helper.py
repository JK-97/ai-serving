import base64
import sandbox

#sandbox._generate_rsa_pair(2048)
sdi = sandbox.default_device_serial()
digest = sandbox.sha256_digest(sdi)
print("sdi:", digest)

ret = sandbox._encrypt_by_public(digest, "./public.pem")
b64key = base64.b64encode(ret)
print("b64(enc(sdi)):", b64key)

ret = sandbox.sha256_recover(b64key, "./private.pem")
sandbox._encrypt(ret, "models", "model_core")
sandbox._decrypt(ret, "model_core", "model_dore")
