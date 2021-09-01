#
#
#   Image encode / decode
#
#

import re
import typer
import humanize
import threading
import bitstring
import numpy as np

from PIL import Image
from queue import Queue
from bitstring import ConstBitStream, BitStream
from utils import bits2string, string2bits, write_bits


LOSSLESS_IMAGE_FORMATS = (".png", ".gif", ".tiff")


app = typer.Typer()


@app.command()
def encode(file_path: str, carrier_path: str, output_path: str):
    assert output_path.lower().endswith(LOSSLESS_IMAGE_FORMATS), \
        "Extension for output must be one of the following: {}".format(", ".join(LOSSLESS_IMAGE_FORMATS))

    input_img = Image.open(carrier_path).convert("RGB")
    output_img = np.array(input_img)

    file_bits = ConstBitStream(filename=file_path)

    max_hidden_file_bits = input_img.width * input_img.height * 3
    if len(file_bits) > max_hidden_file_bits:
        human_readable_max_size = humanize.naturalsize(max_hidden_file_bits / 8)  # convert to bytes
        raise ValueError("Binary value larger than image size. Max file size is {}".format(human_readable_max_size))

    header = "$--{}--$".format(len(file_bits))
    header_bits = BitStream("0b" + string2bits(header))

    bits_iterator = header_bits + file_bits

    for (idx, value) in np.ndenumerate(input_img):
        binary_value = "{0:08b}".format(value)

        try:
            next_bit = bits_iterator.read("bin:1")
        except bitstring.ReadError:
            break
        else:
            output_img[idx] = int(binary_value[:-1] + str(next_bit), 2)

    Image.fromarray(output_img).save(output_path)


@app.command()
def decode(carrier_path: str, output_path: str, write_bytes_interval: int = 1024):
    img = Image.open(carrier_path)

    header_regex = re.compile("^" + string2bits("$--") + r"(?:[0-1]{8})+" + string2bits("--$") + "$")

    queue = Queue()

    thread = threading.Thread(target=write_bits, args=(output_path, queue, write_bytes_interval))
    thread.start()

    hidden_file_length = None
    hidden_file_bits_written = 0

    header_bits = ""

    for (idx, value) in np.ndenumerate(img):
        last_bit = "{0:08b}".format(value)[-1]

        if hidden_file_length is None:
            # header not found yet
            header_bits += last_bit
            header_match = header_regex.match(header_bits)
            if header_match:
                hidden_file_length = int(bits2string(header_match.group()).rstrip("$--").lstrip("--$"))
        else:
            queue.put(last_bit)

            hidden_file_bits_written += 1

            if hidden_file_bits_written >= hidden_file_length:
                break

    queue.put(None)
    thread.join()


if __name__ == "__main__":
    app()
