param(
    [string]$PythonPath = ".\.venv311\Scripts\python.exe",
    [int]$MinCoverage = 95
)

$ErrorActionPreference = "Stop"

if (-not (Test-Path $PythonPath)) {
    throw "Python interpreter not found at: $PythonPath"
}

$covModules = @(
    "Sources.oazix.CustomBehaviors.skills.monitoring.drop_tracker_protocol",
    "Sources.oazix.CustomBehaviors.skills.monitoring.drop_tracker_transport",
    "Sources.oazix.CustomBehaviors.skills.monitoring.drop_tracker_row_ops",
    "Sources.oazix.CustomBehaviors.skills.monitoring.drop_tracker_log_store",
    "Sources.oazix.CustomBehaviors.skills.monitoring.drop_tracker_inventory_actions"
)

$args = @(
    "-m", "pytest",
    "Sources/oazix/CustomBehaviors/tests",
    "-k", "drop_tracker",
    "--maxfail=1",
    "--disable-warnings",
    "--cov-report=term-missing:skip-covered",
    "--cov-fail-under=$MinCoverage"
)

foreach ($mod in $covModules) {
    $args += "--cov=$mod"
}

& $PythonPath @args
exit $LASTEXITCODE
