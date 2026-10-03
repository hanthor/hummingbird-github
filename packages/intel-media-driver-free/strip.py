import os
import shutil
import subprocess
from pathlib import Path

REMOVE_ALL_KERNELS = False

print("Finding out the package version...")
result = subprocess.run(
    ['rpmspec', '-q', '--queryformat=%{VERSION}\n', 'intel-media-driver-free.spec'],
    capture_output=True,
    text=True,
    check=True
)
version = result.stdout.strip().split('\n')[0]
print("Found %s" % version)

source_file = f"intel-media-{version}.tar.gz"
if not os.path.exists(source_file):
    print("Source file not found, downloading...")
    subprocess.run(
        ['wget', f'https://github.com/intel/media-driver/archive/{source_file}'],
        check=True
    )

print("Unpacking...")
subprocess.run(
    ['tar', '-xf', source_file],
    check=True
)

unpacked_dir = Path(f"media-driver-intel-media-{version}")

print("Removing non-free kernels...")
# Remove kernel directories matching pattern
for kernel_path in unpacked_dir.rglob('kernel'):
    if 'gen' in str(kernel_path):
        shutil.rmtree(kernel_path, ignore_errors=True)

# Remove cm_gpucopy_kernel files
for cm_path in unpacked_dir.rglob('cm_gpucopy_kernel*'):
    if cm_path.is_file():
        cm_path.unlink()
    elif cm_path.is_dir():
        shutil.rmtree(cm_path, ignore_errors=True)

# Remove cmrt_kernel directories
for cmrt_path in unpacked_dir.rglob('cmrt_kernel'):
    shutil.rmtree(cmrt_path, ignore_errors=True)

if REMOVE_ALL_KERNELS:
    print("Removing free kernels...")
    for kernel_free_path in unpacked_dir.rglob('kernel_free'):
        if 'gen' in str(kernel_free_path):
            subprocess.run(
                ['git', 'rm', '-r', str(kernel_free_path)],
                cwd=str(unpacked_dir)
            )

print("Stripping non-free files and directories...")

print("Packing back up...")
output_file = f"intel-media-{version}-free.tar.gz"
subprocess.run(
    ['tar', '-czf', output_file, str(unpacked_dir)],
    check=True
)

print("Cleaning up...")
shutil.rmtree(unpacked_dir)

print(f"Done, created {output_file}")
