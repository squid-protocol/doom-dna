"""Copy an IWAD and replace its DEMO1 lump with another demo (appended after the directory; the directory entry is repointed).
For engines that cannot load a second WAD file or an external .lmp. Usage: python make_demo_iwad.py <in.wad> <demo.lmp> <out.wad>"""
import struct, sys
src = bytearray(open(sys.argv[1], "rb").read()); demo = open(sys.argv[2], "rb").read()
ident, n, ofs = struct.unpack("<4sii", src[:12]); assert ident == b"IWAD"
for i in range(n):
    e = ofs + 16 * i
    if bytes(src[e + 8:e + 16]).rstrip(b"\0") == b"DEMO1":
        new = len(src); src += demo; struct.pack_into("<ii", src, e, new, len(demo)); break
else: raise SystemExit("DEMO1 lump not found")
open(sys.argv[3], "wb").write(src)
