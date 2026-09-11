import os
import shutil
import subprocess
from pathlib import Path

REMOVE_ALL_KERNELS = False

print("Finding out the package version...")
spec_path = Path("intel-media-driver-free.spec")
output = subprocess.check_output(
    ["rpmspec", "-q", "--queryformat=%{VERSION}\n", str(spec_path)],
    text=True,
)
version = output.splitlines()[0].strip()
print("Found %s" % version)

tar_name = f"intel-media-{version}.tar.gz"
tar_path = Path(tar_name)

if not tar_path.exists():
    print("Source file not found, downloading...")
    subprocess.run(
        ["wget", f"https://github.com/intel/media-driver/archive/{tar_name}"],
        check=True,
    )

print("Unpacking...")
subprocess.run(["tar", "-xf", tar_name], check=True)

unpacked_dir = Path(f"media-driver-intel-media-{version}")

print("Removing non-free kernels...")
for path in unpacked_dir.rglob("kernel"):
    if "gen" in path.name or "gen" in str(path):
        if path.is_dir():
            shutil.rmtree(path)
        else:
            path.unlink()

for path in unpacked_dir.rglob("cm_gpucopy_kernel*"):
    if path.is_file() or path.is_symlink():
        path.unlink()

for path in unpacked_dir.rglob("cmrt_kernel"):
    if path.is_dir():
        shutil.rmtree(path)
    else:
        path.unlink()

if REMOVE_ALL_KERNELS:
    print("Removing free kernels...")
    for path in unpacked_dir.rglob("kernel_free"):
        if "gen" in path.name or "gen" in str(path):
            if path.is_dir():
                shutil.rmtree(path)

print("Stripping non-free files and directories...")

print("Packing back up...")
out_tar = f"intel-media-{version}-free.tar.gz"
subprocess.run(["tar", "-czf", out_tar, str(unpacked_dir)], check=True)

print("Cleaning up...")
if unpacked_dir.exists():
    shutil.rmtree(unpacked_dir)

print("Done, created %s" % out_tar)
