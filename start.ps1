$ErrorActionPreference = "Stop"

if (Test-Path .env) {
    Get-Content .env | ForEach-Object {
        if ($_ -match "^\s*#" -or $_ -match "^\s*$") { return }
        $name, $value = $_ -split "=", 2
        [System.Environment]::SetEnvironmentVariable($name.Trim(), $value.Trim(), "Process")
    }
}

waitress-serve --host=0.0.0.0 --port=5000 wsgi:app
