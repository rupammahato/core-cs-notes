$ErrorActionPreference = 'Stop'
$base = $PSScriptRoot
$original = Join-Path $base 'outputs/p3-analysis/analysis-practice.xlsx'
$copy = Join-Path $base 'outputs/qa/native-check.xlsx'
Copy-Item -LiteralPath $original -Destination $copy -Force
$excel = $null
$book = $null
$script:checks = @()
try {
    $excel = New-Object -ComObject Excel.Application
    $excel.Visible = $false
    $excel.DisplayAlerts = $false
    $excel.AutomationSecurity = 3
    $book = $excel.Workbooks.Open($copy, 0, $false)
    $analysis = $book.Worksheets.Item('Analysis')
    $sources = $book.Worksheets.Item('Sources')
    function Check-Cell($sheet, $address, $expected, $name) {
        $actual = $sheet.Range($address).Value2
        if ($expected -is [string]) {
            if ($actual -cne $expected) { throw "$name expected $expected; got $actual" }
        } elseif ([Math]::Abs([double]$actual - [double]$expected) -gt 0.000000001) {
            throw "$name expected $expected; got $actual"
        }
        $script:checks += [PSCustomObject]@{ name = $name; passed = $true }
    }
    $excel.CalculateFullRebuild()
    $expected = @(5,4,290,2,'n.a.',110,0,110,0.8)
    for ($i = 0; $i -lt $expected.Count; $i++) { Check-Cell $analysis "B$($i+8)" $expected[$i] "Baseline row $($i+8)" }
    Check-Cell $sources 'A6' '0001' 'Text ID preserves leading zeros'
    Check-Cell $sources 'C6' 'raw: 2026-10-01T00:30:00+05:30' 'Original offset timestamp remains text'
    Check-Cell $sources 'D6' ([datetime]::new(2026,9,30,19,0,0).ToOADate()) 'UTC date is numeric and normalized'
    Check-Cell $analysis 'G13' 7 'Orphan provider amount retained'
    Check-Cell $analysis 'G14' 1 'Orphan attempt count'
    Check-Cell $analysis 'G15' 2 'Date issues visible'
    Check-Cell $analysis 'G16' 1 'Unmapped job visible'
    $sources.Range('F7').Value2 = 250
    $excel.CalculateFullRebuild()
    Check-Cell $analysis 'B10' 340 'Billed amount edit recalculates'
    $sources.Range('F7').Value2 = 200
    $sources.Range('F8').ClearContents()
    $excel.CalculateFullRebuild()
    Check-Cell $analysis 'B11' 3 'Blank differs from numeric zero'
    $sources.Range('F8').Value2 = 0
    $sources.Range('F9').Value2 = 0
    $excel.CalculateFullRebuild()
    Check-Cell $analysis 'B11' 1 'One missing bill remains'
    Check-Cell $analysis 'B12' 'n.a.' 'One prerequisite does not complete total'
    $sources.Range('F10').Value2 = 100
    $excel.CalculateFullRebuild()
    Check-Cell $analysis 'B12' 390 'All billed values enable complete total'
    $sources.Range('F9').ClearContents()
    $sources.Range('F10').ClearContents()
    $sources.Range('J7').ClearContents()
    $excel.CalculateFullRebuild()
    Check-Cell $analysis 'B13' 100 'Partial missing cost retains known subtotal'
    Check-Cell $analysis 'B14' 1 'Missing cost job visible'
    Check-Cell $analysis 'B15' 'n.a.' 'Incomplete provider total withheld'
    $sources.Range('J7').Value2 = 10
    $analysis.Range('E5').Value2 = ([datetime]::new(2026,10,20).ToOADate())
    $excel.CalculateFullRebuild()
    Check-Cell $analysis 'B8' 3 'Changed report endpoint excludes later jobs'
    Check-Cell $analysis 'B12' 290 'Complete total for changed population'
    Check-Cell $analysis 'B13' 70 'Provider cost follows report interval'
    $analysis.Range('E5').Value2 = ([datetime]::new(2026,11,1).ToOADate())
    $sources.Range('N8').Value2 = 'wsA'
    $excel.CalculateFullRebuild()
    Check-Cell $analysis 'C21' 'Duplicate key' 'Ambiguous lookup is not silently first-matched'
    $sources.Range('N8').Value2 = 'wsC'
    $sources.Range('O6').ClearContents()
    $excel.CalculateFullRebuild()
    Check-Cell $analysis 'C21' 'Missing plan' 'Matched blank lookup value remains missing'
    $sources.Range('O6').Value2 = 'paid'
    $excel.CalculateFullRebuild()
    for ($i = 0; $i -lt $expected.Count; $i++) { Check-Cell $analysis "B$($i+8)" $expected[$i] "Restored row $($i+8)" }
    $formulaErrors = @()
    foreach ($sheet in @($analysis,$sources)) {
        foreach ($cell in $sheet.UsedRange.Cells) {
            if ($cell.Text -match '^#(REF!|DIV/0!|VALUE!|NAME\?|N/A|NUM!|NULL!|SPILL!|CALC!)$') {
                $formulaErrors += "$($sheet.Name)!$($cell.Address())"
            }
        }
    }
    if ($formulaErrors.Count -ne 0) { throw "Formula errors: $formulaErrors" }
    $proof = [PSCustomObject]@{
        verified_date = '2026-10-18'; excel_version = $excel.Version; excel_build = $excel.Build
        total = $script:checks.Count; checks = $script:checks; formula_errors = $formulaErrors
        original_file_unchanged = $true; disposable_copy_used = $true; native_pivottable_created = $false
        scope = 'Native Excel recalculation on a disposable copy; source input mutations restored; no workbook or account outside this task changed.'
    }
    $proof | ConvertTo-Json -Depth 8 | Set-Content -LiteralPath (Join-Path $base 'native-excel-validation.json') -Encoding UTF8
    Write-Output "Native Excel checks passed: $($script:checks.Count)"
} finally {
    if ($book) { $book.Close($false) }
    if ($excel) { $excel.Quit() }
    if ($sources) { [void][System.Runtime.InteropServices.Marshal]::FinalReleaseComObject($sources) }
    if ($analysis) { [void][System.Runtime.InteropServices.Marshal]::FinalReleaseComObject($analysis) }
    if ($book) { [void][System.Runtime.InteropServices.Marshal]::FinalReleaseComObject($book) }
    if ($excel) { [void][System.Runtime.InteropServices.Marshal]::FinalReleaseComObject($excel) }
    [GC]::Collect()
    [GC]::WaitForPendingFinalizers()
}
