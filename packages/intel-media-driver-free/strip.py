import os
import shutil
import subprocess
import re

REMOVE_ALL_KERNELS = False

def validate_version(version_str):
    """Validate version string to prevent injection attacks."""
    # Allow alphanumeric, dots, hyphens, underscores
    if not re.match(r'^[a-zA-Z0-9._-]+$', version_str):
        raise ValueError(f"Invalid version format: {version_str}")
    return version_str

print("Finding out the package version...")
result = subprocess.run(
    ["rpmspec", "-q", "--queryformat=%{VERSION}\n", "intel-media-driver-free.spec"],
    capture_output=True,
    text=True,
    check=True
)
version = validate_version(result.stdout.split('\n')[0].strip())
print("Found %s" % version)

if not os.path.exists("intel-media-%s.tar.gz" % version):
    print("Source file not found, downloading...")
    subprocess.run(
        ["wget", "https://github.com/intel/media-driver/archive/intel-media-%s.tar.gz" % version],
        check=True
    )

print("Unpacking...")
subprocess.run(["tar", "-xf", "intel-media-%s.tar.gz" % version], check=True)

unpacked_dir = "media-driver-intel-media-%s" % version

print("Removing non-free kernels...")
subprocess.run(
    ["sh", "-c", "find . -name kernel | grep gen | xargs rm -r"],
    cwd=unpacked_dir,
    check=False
)
subprocess.run(
    ["sh", "-c", "find . -name cm_gpucopy_kernel* | xargs rm"],
    cwd=unpacked_dir,
    check=False
)
subprocess.run(
    ["sh", "-c", "find . -name cmrt_kernel | xargs rm -r"],
    cwd=unpacked_dir,
    check=False
)

if REMOVE_ALL_KERNELS:
    print("Removing free kernels...")
    subprocess.run(
        ["sh", "-c", "find . -name kernel_free | grep gen | xargs git rm -r"],
        cwd=unpacked_dir,
        check=False
    )

print("Stripping non-free files and directories...")

print("Packing back up...")
subprocess.run(
    ["tar", "-czf", "intel-media-%s-free.tar.gz" % version, unpacked_dir],
    check=True
)

print("Cleaning up...")
shutil.rmtree(unpacked_dir)

print("Done, created intel-media-%s-free.tar.gz" % version)
