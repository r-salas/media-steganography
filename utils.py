#
#
#   Utils
#
#

from queue import Queue


def string2bits(s):
    return "".join([bin(ord(x))[2:].zfill(8) for x in s])


def bits2string(b):
    return ''.join(chr(int(''.join(x), 2)) for x in zip(*[iter(b)]*8))


def write_bits(file_path: str, queue: Queue, bytes_interval: int = 1024):
    bits_buffer = ""
    bytes_buffer = bytearray()

    with open(file_path, "wb") as fp:
        while True:
            bit = queue.get()

            if bit is None:
                break

            bits_buffer += bit

            if len(bits_buffer) >= 8:
                bytes_buffer.append(int(bits_buffer, 2))
                bits_buffer = ""

                if len(bytes_buffer) >= bytes_interval:
                    fp.write(bytes_buffer)
                    bytes_buffer.clear()

        if len(bytes_buffer) > 0:
            fp.write(bytes_buffer)


class BitsWriter:

    def __init__(self, file_path, bytes_interval: int = 1024):
        self.file_path = file_path
        self.bytes_interval = bytes_interval

        self._file = open(file_path, "wb")

        self._bits_buffer = ""
        self._bytes_buffer = bytearray()

    def add(self, bit):
        self._bits_buffer += bit

        if len(self._bits_buffer) >= 8:
            self._bytes_buffer.append(int(self._bits_buffer, 2))
            self._bits_buffer = ""

            if len(self._bytes_buffer) >= self.bytes_interval:
                self._file.write(self._bytes_buffer)
                self._bytes_buffer.clear()

    def close(self):
        if len(self._bytes_buffer) > 0:
            self._file.write(self._bytes_buffer)

        self._file.close()
