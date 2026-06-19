import subprocess, sys, os

ko_files = []
for root, dirs, files in os.walk(sys.argv[1]):
    for f in files:
        if f.endswith('.ko'):
            ko_files.append(os.path.join(root, f))

print(f"Found {len(ko_files)} stock .ko files", file=sys.stderr)

symvers = {}
for ko in ko_files:
    try:
        result = subprocess.run(
            ['modprobe', '--dump-modversions', ko],
            capture_output=True, text=True
        )
        for line in result.stdout.splitlines():
            parts = line.strip().split()
            if len(parts) == 2:
                crc, sym = parts
                symvers[sym] = crc
    except Exception:
        pass

print(f"Total unique symbols: {len(symvers)}", file=sys.stderr)
for sym, crc in sorted(symvers.items()):
    print(f"{crc}\t{sym}\t(unknown)\tEXPORT_SYMBOL")
