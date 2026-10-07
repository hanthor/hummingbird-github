import os
import shutil
import subprocess
import sys

REMOVE_ALL_KERNELS = False

def run_cmd(cmd):
    """Run command safely without shell interpretation. Raises on failure."""
    result = subprocess.run(cmd, check=False)
    return result.returncode

def run_cmd_output(cmd):
    """Run command safely and capture output. Raises on failure."""
    result = subprocess.run(cmd, capture_output=True, text=True, check=False)
    if result.returncode != 0:
        raise RuntimeError(f"Command failed: {' '.join(cmd)}\n{result.stderr}")
    return result.stdout

print("Finding out the package version...")
version_output = run_cmd_output(["rpmspec", "-q", "--queryformat=%{VERSION}\n", "intel-media-driver-free.spec"])
version = version_output.split("\n")[0].strip()
print(f"Found {version}")

# Validate version string to prevent directory traversal attacks
if "/" in version or ".." in version or "\\" in version:
    print(f"Invalid version string: {version}", file=sys.stderr)
    sys.exit(1)

source_file = f"intel-media-{version}.tar.gz"
if not os.path.exists(source_file):
    print("Source file not found, downloading...")
    run_cmd(["wget", f"https://github.com/intel/media-driver/archive/intel-media-{version}.tar.gz"])

print("Unpacking...")
run_cmd(["tar", "-xf", source_file])

unpacked_dir = f"media-driver-intel-media-{version}"

print("Removing non-free kernels...")
# Find and remove gen*/kernel directories
result = run_cmd_output(["find", unpacked_dir, "-path", "*/gen*/kernel", "-type", "d"])
for kernel_dir in result.strip().split("\n"):
    if kernel_dir:
        shutil.rmtree(kernel_dir, ignore_errors=True)

# Find and remove cm_gpucopy_kernel* files
result = run_cmd_output(["find", unpacked_dir, "-name", "cm_gpucopy_kernel*", "-type", "f"])
for kernel_file in result.strip().split("\n"):
    if kernel_file and os.path.exists(kernel_file):
        os.remove(kernel_file)

# Find and remove cmrt_kernel directories
result = run_cmd_output(["find", unpacked_dir, "-name", "cmrt_kernel", "-type", "d"])
for kernel_dir in result.strip().split("\n"):
    if kernel_dir:
        shutil.rmtree(kernel_dir, ignore_errors=True)

if REMOVE_ALL_KERNELS:
    print("Removing free kernels...")
    result = run_cmd_output(["find", unpacked_dir, "-path", "*/gen*/kernel_free", "-type", "d"])
    for kernel_dir in result.strip().split("\n"):
        if kernel_dir:
            run_cmd(["git", "rm", "-r", kernel_dir])

print("Stripping non-free files and directories...")

print("Packing back up...")
output_file = f"intel-media-{version}-free.tar.gz"
run_cmd(["tar", "-czf", output_file, unpacked_dir])

print("Cleaning up...")
shutil.rmtree(unpacked_dir)

print(f"Done, created {output_file}")
