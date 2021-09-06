# media-steganography
Steganography files using into images or audio using the Least Significant Bit.

## Installation
```console
$ git clone https://github.com/r-salas/media-steganography
$ cd media-steganography
$ pip install -r requirements.txt
```

## Encode file to image
```console
$ python image.py encode <file> <base_image> <carrier> 
```

For example:
```console
$ python image.py encode examples/secret.txt examples/tree.png examples/hidden.png
```

## Decode file from image
```console
$ python image.py decode <carrier> <file>
```

For example
```console
$ python image.py decode examples/hidden.png examples/decoded.txt
```

## Encode file to audio
```console
$ python audio.py encode <file> <base_audio> <carrier> 
```

For example:
```console
$ python audio.py encode examples/secret.txt examples/cantina.wav examples/hidden.wav
```

## Decode file from audio
```console
$ python audio.py decode <carrier> <file>
```

For example
```console
$ python audio.py decode examples/hidden.wav examples/decoded.txt
```
