# import pyAesCrypt
import os
import shutil
import base64
from Crypto.Cipher import AES
from Crypto.Hash import SHA256
from Crypto import Random


def walk_with_care(path):
    w = list(os.walk(path))[0]
    folders = w[1]
    files = [x for x in w[2] if not (x.startswith('.'))]
    return folders, files


def encrypt(path, key):
    folders, _ = walk_with_care(path)
    for folder in folders:
        full_path = os.path.join(path, folder)
        shutil.make_archive(full_path, 'zip', full_path)
        shutil.rmtree(full_path)

    _, files = walk_with_care(path)
    for fil in files:
        filename = os.path.join(path, fil)
        # uuid, _ = os.path.splitext(filename)
        # uuid = filename + '.aes'
        # print(filename, uuid)
        # pyAesCrypt.encryptFile(filename, uuid, key, 64 * 1024)

        with open(filename, 'rb') as fIn:
            data = fIn.read()
            with open(filename, 'wb') as fOut:
                fOut.write(encrypt_file(key, data, False))
                # pyAesCrypt.encryptStream(fIn, fOut, key, 64 * 1024)
                fOut.close()
            fIn.close()
        size = os.stat(filename).st_size
        print('Enc size:', size)


def decrypt(path, key):
    _, files = walk_with_care(path)
    [print(x) for x in files]
    for fil in files:
        filename = os.path.join(path, fil)
        uuid, _ = os.path.splitext(filename)
        # pyAesCrypt.decryptFile(filename, uuid, key, 64 * 1024)
        size = os.stat(filename).st_size
        with open(filename, 'rb') as fIn:
            data = fIn.read()
            try:
                with open(filename, 'wb') as fOut:
                    print('Dec size2:', size)
                    fOut.write(decrypt_file(key, data, False))
                    # pyAesCrypt.decryptStream(fIn, fOut, key, 64 * 1024, size)
                    fOut.close()
            except ValueError as e:
                print(e)
            fIn.close()

        if fil.endswith('.zip'):
            print('unzipping', fil, '\n\n\n')
            shutil.unpack_archive(filename, filename[:-4], 'zip')
            os.remove(filename)


def encrypt_file(pwd, source, encode=True):
    key = SHA256.new(bytes(pwd, encoding='utf-8')).digest()  # use SHA-256 over our key to get a proper-sized AES key
    IV = Random.new().read(AES.block_size)  # generate IV
    encryptor = AES.new(key, AES.MODE_CBC, IV)
    padding = AES.block_size - len(source) % AES.block_size  # calculate needed padding
    source += bytes([padding]) * padding  # Python 2.x: source += chr(padding) * padding
    data = IV + encryptor.encrypt(source)  # store the IV at the beginning and encrypt
    return base64.b64encode(data).decode("latin-1") if encode else data


def decrypt_file(pwd, source, decode=True):
    if decode:
        source = base64.b64decode(source.encode("latin-1"))
    key = SHA256.new(bytes(pwd, encoding='utf-8')).digest()  # use SHA-256 over our key to get a proper-sized AES key
    IV = source[:AES.block_size]  # extract the IV from the beginning
    decryptor = AES.new(key, AES.MODE_CBC, IV)
    data = decryptor.decrypt(source[AES.block_size:])  # decrypt
    padding = data[-1]  # pick the padding value from the end; Python 2.x: ord(data[-1])
    if data[-padding:] != bytes([padding]) * padding:  # Python 2.x: chr(padding) * padding
        raise ValueError("Invalid padding...")
    return data[:-padding]  # remove the padding
