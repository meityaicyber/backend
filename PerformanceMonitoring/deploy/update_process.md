# Air-Gapped Update Process

1. **Approval**: Obtain managerial approval for the new update via the change control system.
2. **Packaging**: From a trusted internet-connected build server, create the ZIP archive including `vendor/` dependencies and `config/`.
3. **Checksum Manifest**: Run `python deploy/build_offline_package.py` to generate the `SUBMISSION_MANIFEST.json` containing SHA-256 hashes of all files.
4. **Malware Scanning**: Scan the `.zip` archive on the trusted build server.
5. **Chain of Custody**: Transfer the archive to secure removable media and sign the custody log.
6. **Transfer**: Move the media into the air-gapped environment.
7. **Checksum Verification**: Extract the archive and verify the checksums match the manifest exactly.
8. **Installation Verification**: Run `deploy/install_offline.bat`, which installs dependencies locally, followed by `python deploy/verify_install.py` to run the smoke test.
