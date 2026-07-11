# Run the Saturday Preparation Pack

1. Extract this ZIP.
2. Open Windows PowerShell in the extracted folder.
3. Run:

```powershell
Set-ExecutionPolicy -Scope Process Bypass
.\scripts\verify_and_prepare.ps1 -InstallMissing
```

Default repository:

```text
%USERPROFILE%\Documents\PyroGrove\pyrogrove-workflow-diagnostic
```

To use another location:

```powershell
.\scripts\verify_and_prepare.ps1 `
  -RepoRoot "C:\path\pyrogrove-workflow-diagnostic" `
  -InstallMissing
```

When Git identity is not already configured, re-run with your actual Git identity:

```powershell
.\scripts\verify_and_prepare.ps1 `
  -InstallMissing `
  -GitName "Your Git display name" `
  -GitEmail "your-actual-git-email@example.com"
```

Do not invent an email address merely to make the tag pass.

Evidence generated:

```text
evidence\environment\prep-verification.json
evidence\environment\prep-verification.txt
```

Return the contents of `prep-verification.txt` to the chat.

No project-specific application logic is included in this pack.


## If Python is not installed

Install Python 3. During installation, enable `Add python.exe to PATH`. Then close PowerShell, open a new PowerShell window, and rerun the preparation command.
