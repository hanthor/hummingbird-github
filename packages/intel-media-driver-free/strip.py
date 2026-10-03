import os
import re
import shlex
import shutil
import subprocess

REMOVE_ALL_KERNELS = False


def run_command(args, shell=False, **kwargs):
    """Safe wrapper for subprocess.run with error handling."""
    result = subprocess.run(args, shell=shell, capture_output=True, text=True, check=False, **kwargs)
    if result.returncode != 0:
        raise RuntimeError(f"Command failed: {' '.join(args) if isinstance(args, list) else args}\n{result.stderr}")
    return result.stdout


def validate_version(version_str):
    """Validate version string format to prevent injection."""
    # Allow alphanumeric, dots, hyphens, underscores
    if not re.match(r'^[a-zA-Z0-9._-]+$', version_str):
        raise ValueError(f"Invalid version format: {version_str}")
    return version_str


print("Finding out the package version...")
# Use subprocess without shell=True for safety
version_output = run_command(
    ["rpmspec", "-q", "--queryformat=%{VERSION}\n", "intel-media-driver-free.spec"],
    cwd="."
)
version = validate_version(version_output.strip().split('\n')[0])
print(f"Found {version}")

source_file = f"intel-media-{version}.tar.gz"
if not os.path.exists(source_file):
    print("Source file not found, downloading...")
    # Use subprocess.run with list arguments instead of shell command
    run_command(
        ["wget", "-O", source_file, f"https://github.com/intel/media-driver/archive/intel-media-{version}.tar.gz"],
        cwd="."
    )

print("Unpacking...")
run_command(["tar", "-xf", source_file], cwd=".")

unpacked_dir = f"media-driver-intel-media-{version}"

print("Removing non-free kernels...")
# Use find with subprocess instead of os.system
run_command(
    ["find", ".", "-name", "kernel", "-path", "*/gen*", "-type", "d", "-exec", "rm", "-rf", "{}", "+"],
    cwd=unpacked_dir
)
run_command(
    ["find", ".", "-name", "cm_gpucopy_kernel*", "-type", "f", "-delete"],
    cwd=unpacked_dir
)
run_command(
    ["find", ".", "-name", "cmrt_kernel", "-type", "d", "-exec", "rm", "-rf", "{}", "+"],
    cwd=unpacked_dir
)

if REMOVE_ALL_KERNELS:
    print("Removing free kernels...")
    run_command(
        ["find", ".", "-name", "kernel_free", "-path", "*/gen*", "-type", "d", "-exec", "rm", "-rf", "{}", "+"],
        cwd=unpacked_dir
    )

print("Stripping non-free files and directories...")

print("Packing back up...")
output_file = f"intel-media-{version}-free.tar.gz"
run_command(["tar", "-czf", output_file, unpacked_dir], cwd=".")

print("Cleaning up...")
shutil.rmtree(unpacked_dir)

print(f"Done, created {output_file}")
