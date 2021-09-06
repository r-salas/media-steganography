#
#
#   Audio steganography
#
#

import re
import typer
import humanize
import bitstring
import numpy as np
import soundfile as sf

from tqdm import tqdm
from bitstring import ConstBitStream, BitStream, BitArray
from utils import bits2string, string2bits, BitsWriter


app = typer.Typer()


@app.command()
def encode(file_path, input_path, carrier_path):
    assert carrier_path.lower().endswith(".wav"), "Extension for carrier must be .wav"

    input_audio, input_samplerate = sf.read(input_path, dtype="int16")
    output_data, output_samplerate = input_audio.copy(), input_samplerate

    file_bits = ConstBitStream(filename=file_path)

    if len(file_bits) > output_data.size:
        human_readable_max_size = humanize.naturalsize(output_data.size / 8)  # convert to bytes
        raise ValueError("Binary value larger than audio size. Max file size is {}".format(human_readable_max_size))

    header = "$--{}--$".format(len(file_bits))
    header_bits = BitStream("0b" + string2bits(header))

    bits_iterator = header_bits + file_bits

    pbar = tqdm(total=len(bits_iterator))

    for (idx, value) in np.ndenumerate(input_audio):
        binary_value = BitArray(int=value, length=16)

        try:
            next_bit = bits_iterator.read("bin:1")
        except bitstring.ReadError:
            break
        else:
            binary_value[-1] = "0b" + next_bit
            output_data[idx] = binary_value.int
            pbar.update(1)

    sf.write(carrier_path, output_data, output_samplerate, "PCM_24")


@app.command()
def decode(carrier_path, file_path: str, write_bytes_interval: int = 1024):
    carrier_audio, carrier_samplerate = sf.read(carrier_path, dtype="int16")

    header_regex = re.compile("^" + string2bits("$--") + r"(?:[0-1]{8})+" + string2bits("--$") + "$")

    bits_writer = BitsWriter(file_path, write_bytes_interval)

    hidden_file_length = None
    hidden_file_bits_written = 0

    header_bits = ""

    pbar = None

    for (idx, value) in np.ndenumerate(carrier_audio):
        binary_value = BitArray(int=value, length=16)

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
