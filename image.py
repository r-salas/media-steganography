#
#
#   Image encode / decode
#
#

import re
import typer
import humanize
import bitstring
import numpy as np

from PIL import Image
from tqdm import tqdm
from utils import bits2string, string2bits, BitsWriter
from bitstring import ConstBitStream, BitStream, BitArray


LOSSLESS_IMAGE_FORMATS = (".png", ".gif", ".tiff")


app = typer.Typer()


@app.command()
def encode(file_path: str, input_path: str, carrier_path: str):
    assert carrier_path.lower().endswith(LOSSLESS_IMAGE_FORMATS), \
        "Extension for carrier must be one of the following: {}".format(", ".join(LOSSLESS_IMAGE_FORMATS))

    input_img = Image.open(input_path).convert("RGB")
    output_img = np.array(input_img)

    file_bits = ConstBitStream(filename=file_path)

    if len(file_bits) > output_img.size:
        human_readable_max_size = humanize.naturalsize(output_img.size / 8)  # convert to bytes
        raise ValueError("Binary value larger than image size. Max file size is {}".format(human_readable_max_size))

    header = "$--{}--$".format(len(file_bits))
    header_bits = BitStream("0b" + string2bits(header))

    bits_iterator = header_bits + file_bits

    pbar = tqdm(total=len(bits_iterator))

    for (idx, value) in np.ndenumerate(input_img):
        binary_value = BitArray(uint=value, length=8)

        try:
            next_bit = bits_iterator.read("bin:1")
        except bitstring.ReadError:
            break
        else:
            binary_value[-1] = "0b" + next_bit
            output_img[idx] = binary_value.int
            pbar.update(1)

    Image.fromarray(output_img).save(carrier_path)


@app.command()
def decode(carrier_path: str, file_path: str, write_bytes_interval: int = 1024):
    img = Image.open(carrier_path)

    header_regex = re.compile("^" + string2bits("$--") + r"(?:[0-1]{8})+" + string2bits("--$") + "$")

    bits_writer = BitsWriter(file_path, write_bytes_interval)

    hidden_file_length = None
    hidden_file_bits_written = 0

    header_bits = ""

    pbar = None

    for (idx, value) in np.ndenumerate(img):
        binary_value = BitArray(uint=value, length=8)

        last_bit = binary_value.bin[-1]

        # check if header has been found
        if hidden_file_length is None:
            header_bits += last_bit
            header_match = header_regex.match(header_bits)
            if header_match:
                hidden_file_length = int(bits2string(header_match.group()).rstrip("$--").lstrip("--$"))
                pbar = tqdm(total=hidden_file_length)
        else:
            bits_writer.add(last_bit)

            hidden_file_bits_written += 1

            pbar.update(1)

            if hidden_file_bits_written >= hidden_file_length:
                break

    bits_writer.close()


if __name__ == "__main__":
    app()
