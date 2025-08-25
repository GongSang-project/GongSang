from Crypto.Cipher import AES
from Crypto.Util.Padding import pad, unpad
from django.conf import settings
import base64

ENCRYPTION_KEY = settings.ENCRYPTION_KEY

def encrypt_image(image_file):
    try:
        padded_data = pad(image_file.read(), AES.block_size)

        cipher = AES.new(ENCRYPTION_KEY, AES.MODE_CBC)
        encrypted_data = cipher.encrypt(padded_data)

        return base64.b64encode(cipher.iv + encrypted_data)
    except Exception as e:
        print(f"암호화 오류: {e}")
        return None


def decrypt_image(encrypted_data):
    try:
        decoded_data = base64.b64decode(encrypted_data)

        # IV(초기화 벡터)와 암호화된 데이터 분리
        iv = decoded_data[:AES.block_size]
        encrypted_data = decoded_data[AES.block_size:]

        cipher = AES.new(ENCRYPTION_KEY, AES.MODE_CBC, iv)
        decrypted_data = cipher.decrypt(encrypted_data)

        return unpad(decrypted_data, AES.block_size)
    except Exception as e:
        print(f"복호화 오류: {e}")
        return None