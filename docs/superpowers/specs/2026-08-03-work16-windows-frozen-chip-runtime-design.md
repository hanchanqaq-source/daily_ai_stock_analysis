# Work16 Windows Frozen Chip Runtime Design

## Goal

Make the already-installed Windows `mini-racer` runtime available to the PyInstaller
backend and prove the chip module can initialize V8 from both the build output and the
final extracted portable ZIP.

## Evidence and root cause

The fixed `main@568e26adf0e6393a7a0da1be57369535735cd05a` Windows CI resolves
`akshare 1.18.81`, whose Windows dependency is `mini-racer>=0.12.4`; the observed build
installed `mini-racer 0.14.1`. Its wheel contains
`py_mini_racer/mini_racer.dll` and `py_mini_racer/icudtl.dat`. The runtime explicitly
loads those paths from `sys._MEIPASS/py_mini_racer` under PyInstaller.

The current Windows build collects AkShare data but not the `py_mini_racer` package.
Its probes import selected modules and start HTTP endpoints without constructing a
`MiniRacer`, so a healthy frozen backend does not prove that the chip engine can load.

## Minimal design

- Keep `requirements.txt` unchanged and use the transitive Windows runtime that AkShare
  already installs.
- Add PyInstaller collection for `py_mini_racer`, covering Python modules, the DLL and
  ICU data without hand-copying version-specific site-packages paths.
- Fail the build if the packaged DLL or ICU data is missing.
- Add an early, opt-in packaged runtime probe that imports AkShare's
  `stock_feature.stock_cyq_em` module, constructs `MiniRacer`, evaluates deterministic
  JavaScript and exits without network access.
- Invoke the probe from the shared frozen-backend verifier. Because CI and the release
  workflow already use that verifier after extracting the final ZIP, the same contract
  covers both the direct build and final portable artifact.

## Error handling and boundaries

Any missing file, DLL load failure, ICU initialization failure, chip module import
failure or incorrect JavaScript result returns a non-zero process exit and fails the
existing packaging gate. The probe never calls Eastmoney or any other network source.
No fallback hides a failed chip runtime.

This Work does not change dependency declarations, chip calculations, data-source
priority, macOS packaging, news, signing, versions, releases or Windows real-machine
acceptance.

## Testing

TDD static contracts first fail on the fixed Base because collection, asset checks and
the packaged chip probe are absent. After the minimal implementation, those contracts
must pass. The fixed-Head Windows CI then supplies the platform proof: the direct frozen
tree and final extracted portable ZIP must both load the DLL and evaluate JavaScript.
All other applicable CI jobs must remain green.
