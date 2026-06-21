import struct, sys, subprocess

def load_stock_crcs(path):
    crcs = {}
    with open(path) as f:
        for line in f:
            parts = line.strip().split()
            if len(parts) >= 2:
                crcs[parts[1]] = int(parts[0], 16)
    return crcs

def get_needed_symbols(ko_path):
    # Use nm to get undefined symbols this module needs
    result = subprocess.run(
        ['aarch64-linux-gnu-nm', '-u', ko_path],
        capture_output=True, text=True
    )
    syms = []
    for line in result.stdout.splitlines():
        line = line.strip()
        if line.startswith('U '):
            syms.append(line[2:].strip())
    return syms

def build_versions_section(symbols, stock_crcs):
    # Each entry: 4 bytes CRC (LE) + 60 bytes null-padded name = 64 bytes
    data = b''
    count = 0
    for sym in symbols:
        if sym in stock_crcs:
            crc = stock_crcs[sym]
            name_bytes = sym.encode('ascii')[:55]
            entry = struct.pack('<I', crc) + name_bytes + b'\x00' * (60 - len(name_bytes))
            data += entry
            count += 1
    return data, count

if __name__ == '__main__':
    stock_symvers = sys.argv[1]
    ko_path = sys.argv[2]
    out_bin = sys.argv[3]

    stock_crcs = load_stock_crcs(stock_symvers)
    needed = get_needed_symbols(ko_path)
    data, count = build_versions_section(needed, stock_crcs)

    with open(out_bin, 'wb') as f:
        f.write(data)

    print(f"{ko_path}: {count}/{len(needed)} needed symbols matched to stock CRCs, wrote {len(data)} bytes")
