import os
import subprocess
import glob
from setuptools import setup, Command

class CompileProtos(Command):
    """Custom command to compile protocol buffers."""
    description = 'compile protobuf files to python'
    user_options = []

    def initialize_options(self):
        pass

    def finalize_options(self):
        pass

    def run(self):
        root_dir = os.path.dirname(os.path.abspath(__file__))
        out_dir = os.path.join(root_dir, "lynk/shared/proto")
        
        if not os.path.exists(out_dir):
            os.makedirs(out_dir)
            print(f"Created directory: {out_dir}")

        # Find all proto files
        proto_files = []
        proto_files.extend(glob.glob(os.path.join(root_dir, "msg/telemetry/*.proto")))
        proto_files.extend(glob.glob(os.path.join(root_dir, "msg/command/*.proto")))
        proto_files.extend(glob.glob(os.path.join(root_dir, "msg/ack/*.proto")))
        proto_files.extend(glob.glob(os.path.join(root_dir, "msg/result/*.proto")))
        proto_files.extend(glob.glob(os.path.join(root_dir, "msg/event/*.proto")))
        proto_files.extend(glob.glob(os.path.join(root_dir, "msg/mavlink/*.proto")))
        
        nanopb_proto = os.path.join(root_dir, "nanopb.proto")
        if os.path.exists(nanopb_proto):
            proto_files.append(nanopb_proto)

        if not proto_files:
            print("No proto files found.")
            return

        print(f"Found {len(proto_files)} proto files. Compiling...")

        protoc_cmd = [
            "protoc",
            f"-I={root_dir}",
            f"--python_out={out_dir}",
        ] + proto_files

        try:
            subprocess.check_call(protoc_cmd)
            # Create __init__.py
            with open(os.path.join(out_dir, "__init__.py"), "a"):
                os.utime(os.path.join(out_dir, "__init__.py"), None)
            print(f"[OK] Generated Python protobuf modules into {out_dir}")
        except subprocess.CalledProcessError as e:
            print(f"[ERROR] Protobuf compilation failed: {e}")
        except FileNotFoundError:
            print("[ERROR] 'protoc' not found. Please install protobuf compiler.")

if __name__ == "__main__":
    import sys
    # If no arguments provided (e.g. F5 in IDE), default to 'protos' command
    if len(sys.argv) == 1:
        sys.argv.append("protos")

    setup(
        name='lynk-toolkit',
        version='1.1.0',
        packages=['lynk'],
        install_requires=[
            'pyserial',
            'crcmod',
            'PyYAML',
            'protobuf<3.21',
            'fastapi',
            'uvicorn'
        ],
        extras_require={
            'dev': [
                'pytest',
                'pytest-asyncio',
                'httpx'
            ],
        },
        entry_points={
            'console_scripts': [
                'lynk-lab=test_lab:main',
            ],
        },
        cmdclass={
            'protos': CompileProtos,
        },
        description='Mission-critical LYNK Toolkit with automated Test Lab.',
        author='LYNK Mission Control',
    )
