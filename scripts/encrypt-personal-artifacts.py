#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-or-later
"""Return personal builds as age ciphertext; never upload plaintext binaries."""
import argparse
import glob
import hashlib
import json
import os
from pathlib import Path
import subprocess
import tarfile
import tempfile
import urllib.request
import zipfile

ROOT = Path(__file__).resolve().parents[1]
AGE_VERSION = 'v1.3.2'
ARCHIVES = {
    'windows': ('windows-amd64.zip', 'f48d8f8f9ebe903ab5027ed067652f2cc1db94bc206976430133b905dcd8e8c7'),
    'linux': ('linux-amd64.tar.gz', 'cbe24006683f8eb669266162894b9a522a1af52f2665fbc63a4bb032ed26ac10'),
}

def sha256(path):
    digest = hashlib.sha256()
    with path.open('rb') as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b''):
            digest.update(block)
    return digest.hexdigest()

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', required=True, type=Path)
    parser.add_argument('files', nargs='+', help='file paths or glob patterns')
    args = parser.parse_args()
    files = sorted({Path(path).resolve() for pattern in args.files for path in glob.glob(pattern)})
    if not files or any(not path.is_file() for path in files):
        parser.error('no input files, or an input is not a regular file')
    if len({path.name for path in files}) != len(files):
        parser.error('duplicate input filename')
    recipient = (ROOT / '.github/artifact-recipient.txt').read_text().strip()
    if not recipient.startswith('age1') or len(recipient) != 62:
        parser.error('expected one age X25519 recipient in .github/artifact-recipient.txt')
    args.output.mkdir(parents=True, exist_ok=True)
    platform = 'windows' if os.name == 'nt' else 'linux'
    archive, expected = ARCHIVES[platform]
    url = f'https://github.com/FiloSottile/age/releases/download/{AGE_VERSION}/age-{AGE_VERSION}-{archive}'
    manifest = {
        'repository': os.environ.get('GITHUB_REPOSITORY'),
        'commit': os.environ.get('GITHUB_SHA'),
        'run_id': os.environ.get('GITHUB_RUN_ID'),
        'upstream': 'thtbee/nectarlink@58e530f27726aee19a66746576b0e6c764d4278d',
        'files': [],
    }
    with tempfile.TemporaryDirectory(prefix='personal-age-') as temp:
        directory = Path(temp)
        download = directory / archive
        with urllib.request.urlopen(url, timeout=60) as response:
            download.write_bytes(response.read())
        if sha256(download) != expected:
            raise RuntimeError('age archive checksum mismatch')
        member = 'age/age.exe' if platform == 'windows' else 'age/age'
        executable = directory / Path(member).name
        if platform == 'windows':
            with zipfile.ZipFile(download) as packed:
                executable.write_bytes(packed.read(member))
        else:
            with tarfile.open(download) as packed:
                executable.write_bytes(packed.extractfile(member).read())
            executable.chmod(0o700)
        for path in files:
            encrypted = args.output / (path.name + '.age')
            subprocess.run([str(executable), '--encrypt', '--recipient', recipient,
                            '--output', str(encrypted), str(path)], check=True)
            manifest['files'].append({
                'name': path.name, 'size': path.stat().st_size,
                'sha256': sha256(path), 'ciphertext_sha256': sha256(encrypted),
            })
            print(f'Encrypted {path.name} ({path.stat().st_size} bytes)')
    (args.output / 'manifest.json').write_text(json.dumps(manifest, indent=2) + '\n', encoding='utf-8')

if __name__ == '__main__':
    main()
