"""Wrap a demo lump file in a one-lump PWAD (for engines whose external-lump loader is broken). Usage: python lmp2wad.py <in.lmp> <out.wad> <LUMPNAME>"""
import struct, sys
data = open(sys.argv[1], "rb").read(); name = sys.argv[3].upper().encode()[:8].ljust(8, b"\0")
hdr = b"PWAD" + struct.pack("<ii", 1, 12 + len(data))
open(sys.argv[2], "wb").write(hdr + data + struct.pack("<ii", 12, len(data)) + name)
