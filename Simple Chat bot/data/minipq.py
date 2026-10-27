"""Minimal pure-Python parquet reader (thrift compact + snappy + plain/dictionary)."""
import struct


class TReader:
    def __init__(self, b, pos=0):
        self.b, self.p = b, pos

    def byte(self):
        v = self.b[self.p]; self.p += 1; return v

    def varint(self):
        r = s = 0
        while True:
            x = self.byte(); r |= (x & 0x7F) << s; s += 7
            if not x & 0x80: return r

    def zz(self):
        v = self.varint(); return (v >> 1) ^ -(v & 1)

    def binary(self):
        n = self.varint(); v = self.b[self.p:self.p + n]; self.p += n; return bytes(v)

    def val(self, t):
        if t == 1: return True
        if t == 2: return False
        if t == 3: return struct.unpack('b', bytes([self.byte()]))[0]
        if t in (4, 5, 6): return self.zz()
        if t == 7: v = struct.unpack('<d', self.b[self.p:self.p + 8])[0]; self.p += 8; return v
        if t == 8: return self.binary()
        if t in (9, 10):
            h = self.byte(); n = h >> 4; et = h & 0x0F
            if n == 15: n = self.varint()
            return [self.val(et) for _ in range(n)]
        if t == 11:
            n = self.varint()
            if n == 0: return {}
            kv = self.byte(); kt, vt = kv >> 4, kv & 0x0F
            return {self.val(kt): self.val(vt) for _ in range(n)}
        if t == 12: return self.struct()
        raise ValueError('type %d' % t)

    def struct(self):
        out, last = {}, 0
        while True:
            h = self.byte()
            if h == 0: return out
            t = h & 0x0F; d = h >> 4
            fid = last + d if d else self.zz()
            out[fid] = self.val(t); last = fid


def snappy(buf):
    r = TReader(buf); n = r.varint(); out = bytearray(); b = buf; p = r.p
    while p < len(b):
        tag = b[p]; p += 1; k = tag & 3
        if k == 0:
            ln = tag >> 2
            if ln >= 60:
                nb = ln - 59; ln = int.from_bytes(b[p:p + nb], 'little'); p += nb
            ln += 1; out += b[p:p + ln]; p += ln; continue
        if k == 1:
            ln = ((tag >> 2) & 7) + 4; off = ((tag >> 5) << 8) | b[p]; p += 1
        elif k == 2:
            ln = (tag >> 2) + 1; off = int.from_bytes(b[p:p + 2], 'little'); p += 2
        else:
            ln = (tag >> 2) + 1; off = int.from_bytes(b[p:p + 4], 'little'); p += 4
        start = len(out) - off
        if off >= ln: out += out[start:start + ln]
        else:
            for i in range(ln): out.append(out[start + i])
    assert len(out) == n
    return bytes(out)


def rle_hybrid(b, p, end, bw, count):
    out = []; byte_w = (bw + 7) // 8
    while len(out) < count and p < end:
        r = TReader(b, p); h = r.varint(); p = r.p
        if h & 1:
            groups = h >> 1; nbytes = groups * bw
            chunk = int.from_bytes(b[p:p + nbytes], 'little'); p += nbytes
            mask = (1 << bw) - 1
            for i in range(groups * 8): out.append((chunk >> (i * bw)) & mask)
        else:
            run = h >> 1; v = int.from_bytes(b[p:p + byte_w], 'little'); p += byte_w
            out.extend([v] * run)
    return out[:count]


def plain(b, p, ptype, n):
    vals = []
    for _ in range(n):
        if ptype == 6:
            ln = int.from_bytes(b[p:p + 4], 'little'); p += 4; vals.append(b[p:p + ln].decode('utf-8', 'replace')); p += ln
        elif ptype == 2: vals.append(struct.unpack('<q', b[p:p + 8])[0]); p += 8
        elif ptype == 1: vals.append(struct.unpack('<i', b[p:p + 4])[0]); p += 4
        else: raise ValueError(ptype)
    return vals


class ParquetFile:
    def __init__(self, path):
        self.f = open(path, 'rb')
        self.f.seek(-8, 2); n = struct.unpack('<I', self.f.read(4))[0]
        self.f.seek(-8 - n, 2); self.meta = TReader(self.f.read(n)).struct()
        self.schema = self.meta[2]
        self.cols = [s[4].decode() for s in self.schema[1:]]
        self.optional = {s[4].decode(): s.get(3) == 1 for s in self.schema[1:]}
        self.row_groups = self.meta[4]

    def read_column(self, rg_index, name):
        rg = self.row_groups[rg_index]
        cc = rg[1][self.cols.index(name)]; md = cc[3]
        ptype, codec, nvals = md[1], md[4], md[5]
        start = md.get(11) or md[9]
        if md.get(11) and md[11] > md[9]: start = md[9]
        self.f.seek(start); data = self.f.read(md[7])
        p = 0; dic = None; out = []
        while len(out) < nvals and p < len(data):
            r = TReader(data, p); ph = r.struct(); p = r.p
            csize = ph[3]; body = data[p:p + csize]; p += csize
            ptype_page = ph[1]
            if ptype_page == 2:
                raw = snappy(body) if codec == 1 else body
                dic = plain(raw, 0, ptype, ph[7][1]); continue
            if ptype_page == 0:
                raw = snappy(body) if codec == 1 else body
                n = ph[5][1]; enc = ph[5][2]; q = 0
                if self.optional[name]:
                    ln = int.from_bytes(raw[0:4], 'little'); defs = rle_hybrid(raw, 4, 4 + ln, 1, n); q = 4 + ln
                else: defs = [1] * n
            elif ptype_page == 3:
                h = ph[8]; n = h[1]; enc = h[4]; dl = h.get(5, 0); rl = h.get(6, 0)
                lv = body[:rl + dl]
                defs = rle_hybrid(lv, rl, rl + dl, 1, n) if (self.optional[name] and dl) else [1] * n
                rest = body[rl + dl:]
                raw = snappy(rest) if (codec == 1 and h.get(7, True)) else rest; q = 0
            else: continue
            nn = sum(defs)
            if enc in (2, 8):
                bw = raw[q]; idx = rle_hybrid(raw, q + 1, len(raw), bw, nn); vals = [dic[i] for i in idx]
            else: vals = plain(raw, q, ptype, nn)
            it = iter(vals)
            out.extend(next(it) if d else None for d in defs)
        return out
