# Windows signing readiness gate

Work23 evaluates the Windows signing path without acquiring, reading, or
writing any real signing identity. The candidate build remains unsigned unless
a separately authorized workflow later supplies an approved identity.

## Implemented interface

`scripts/verify-windows-installer.ps1` performs a read-only Windows
`Get-AuthenticodeSignature` inspection of both the installer and the installed
application executable. It reports only these sanitized fields:

- `WINDOWS_SIGNATURE_POLICY`;
- `WINDOWS_INSTALLER_SIGNATURE_STATUS`; and
- `WINDOWS_APP_SIGNATURE_STATUS`.

The default policy is `AUDIT_ONLY`, so an unsigned draft candidate can complete
all non-signing lifecycle checks while retaining a truthful `NotSigned` result.
Passing `-RequireValidSignature` changes the policy to `REQUIRE_VALID` and fails
closed unless each inspected status is exactly `Valid` according to the Windows
trust provider. The interface accepts no certificate, key, password, subject,
thumbprint, or secret parameter.

## Separate authorization gate

A production signature requires decisions and authority that Work23 does not
have: the legal publisher identity, certificate type/provider, protected key
custody mechanism, timestamping policy, CI secret boundary, rotation/revocation
procedure, and authorized operators. No certificate purchase or enrollment, no
private-key or certificate read/write, and no CI-secret creation or access is
performed here.

Until that separate authorization is granted and an approved identity is
provisioned outside this work, the correct result is:

`SIGNING_IDENTITY_GATE — candidate lifecycle may pass; production signing may not.`
