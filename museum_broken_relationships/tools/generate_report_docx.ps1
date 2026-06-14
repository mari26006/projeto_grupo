param(
    [string]$InputPath = "RELATORIO_TECNICO_REVISTO.md",
    [string]$OutputPath = "relatorio_museum_broken_relationships_alinhado.docx"
)

$ErrorActionPreference = "Stop"

Add-Type -AssemblyName System.IO.Compression
Add-Type -AssemblyName System.IO.Compression.FileSystem
Add-Type -AssemblyName System.Security

function Escape-Xml([string]$Text) {
    return [System.Security.SecurityElement]::Escape($Text)
}

function New-Run([string]$Text, [bool]$Bold = $false, [int]$Size = 22) {
    $properties = "<w:rPr><w:sz w:val=`"$Size`"/><w:szCs w:val=`"$Size`"/>"
    if ($Bold) {
        $properties += "<w:b/>"
    }
    $properties += "</w:rPr>"
    return "<w:r>$properties<w:t xml:space=`"preserve`">$(Escape-Xml $Text)</w:t></w:r>"
}

function New-Paragraph([string]$Text, [string]$Style = "Normal") {
    $size = 22
    $bold = $false
    $before = 0
    $after = 120

    switch ($Style) {
        "Title" { $size = 34; $bold = $true; $before = 0; $after = 180 }
        "Heading1" { $size = 28; $bold = $true; $before = 260; $after = 120 }
        "Heading2" { $size = 24; $bold = $true; $before = 200; $after = 100 }
        "Bullet" { $size = 22; $before = 0; $after = 70 }
        "Code" { $size = 19; $before = 0; $after = 40 }
    }

    $indent = if ($Style -eq "Bullet") { '<w:ind w:left="420" w:hanging="220"/>' } elseif ($Style -eq "Code") { '<w:ind w:left="420"/>' } else { "" }
    $prefix = if ($Style -eq "Bullet") { "• " } else { "" }
    $spacing = "<w:spacing w:before=`"$before`" w:after=`"$after`"/>"
    return "<w:p><w:pPr>$spacing$indent</w:pPr>$(New-Run ($prefix + $Text) $bold $size)</w:p>"
}

function New-Table([System.Collections.Generic.List[string[]]]$Rows) {
    if ($Rows.Count -eq 0) {
        return ""
    }

    $xml = '<w:tbl><w:tblPr><w:tblBorders><w:top w:val="single" w:sz="4" w:color="C2607A"/><w:left w:val="single" w:sz="4" w:color="C2607A"/><w:bottom w:val="single" w:sz="4" w:color="C2607A"/><w:right w:val="single" w:sz="4" w:color="C2607A"/><w:insideH w:val="single" w:sz="4" w:color="D9B3BD"/><w:insideV w:val="single" w:sz="4" w:color="D9B3BD"/></w:tblBorders></w:tblPr>'
    for ($rowIndex = 0; $rowIndex -lt $Rows.Count; $rowIndex++) {
        $xml += "<w:tr>"
        foreach ($cell in $Rows[$rowIndex]) {
            $bold = $rowIndex -eq 0
            $xml += "<w:tc><w:tcPr><w:tcW w:w=`"3000`" w:type=`"dxa`"/></w:tcPr><w:p><w:pPr><w:spacing w:after=`"60`"/></w:pPr>$(New-Run $cell $bold 19)</w:p></w:tc>"
        }
        $xml += "</w:tr>"
    }
    return $xml + "</w:tbl><w:p/>"
}

$markdown = Get-Content -LiteralPath $InputPath -Encoding UTF8
$body = New-Object System.Text.StringBuilder
$tableRows = New-Object 'System.Collections.Generic.List[string[]]'
$inCode = $false

function Flush-Table {
    if ($tableRows.Count -gt 0) {
        [void]$body.Append((New-Table $tableRows))
        $tableRows.Clear()
    }
}

foreach ($line in $markdown) {
    if ($line -match '^```') {
        Flush-Table
        $inCode = -not $inCode
        continue
    }

    if ($inCode) {
        [void]$body.Append((New-Paragraph $line "Code"))
        continue
    }

    if ($line -match '^\|(.+)\|$') {
        if ($line -match '^\|[\s\-|]+\|$') {
            continue
        }
        $cells = $line.Trim('|').Split('|') | ForEach-Object { $_.Trim().Replace('`', '') }
        $tableRows.Add([string[]]$cells)
        continue
    }

    Flush-Table

    if ($line -match '^# (.+)$') {
        [void]$body.Append((New-Paragraph $Matches[1] "Title"))
    } elseif ($line -match '^## (.+)$') {
        [void]$body.Append((New-Paragraph $Matches[1] "Heading1"))
    } elseif ($line -match '^### (.+)$') {
        [void]$body.Append((New-Paragraph $Matches[1] "Heading2"))
    } elseif ($line -match '^- (.+)$') {
        [void]$body.Append((New-Paragraph ($Matches[1].Replace('`', '')) "Bullet"))
    } elseif ($line -match '^\d+\. (.+)$') {
        [void]$body.Append((New-Paragraph $line "Bullet"))
    } elseif ($line -eq '---') {
        [void]$body.Append('<w:p><w:pPr><w:pBdr><w:bottom w:val="single" w:sz="8" w:color="C2607A"/></w:pBdr><w:spacing w:after="120"/></w:pPr></w:p>')
    } elseif ([string]::IsNullOrWhiteSpace($line)) {
        [void]$body.Append('<w:p/>')
    } else {
        $plain = $line.Replace('**', '').Replace('`', '').Replace('*', '')
        [void]$body.Append((New-Paragraph $plain))
    }
}
Flush-Table

$documentXml = @"
<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">
<w:body>
$body
<w:sectPr>
<w:pgSz w:w="11906" w:h="16838"/>
<w:pgMar w:top="1134" w:right="1134" w:bottom="1134" w:left="1134" w:header="708" w:footer="708" w:gutter="0"/>
</w:sectPr>
</w:body>
</w:document>
"@

$contentTypes = @"
<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">
<Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>
<Default Extension="xml" ContentType="application/xml"/>
<Override PartName="/word/document.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.document.main+xml"/>
</Types>
"@

$relationships = @"
<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
<Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="word/document.xml"/>
</Relationships>
"@

$outputFullPath = [System.IO.Path]::GetFullPath($OutputPath)
$tempDirectory = Join-Path ([System.IO.Path]::GetTempPath()) ("museum-report-" + [guid]::NewGuid().ToString())
New-Item -ItemType Directory -Path (Join-Path $tempDirectory "_rels") -Force | Out-Null
New-Item -ItemType Directory -Path (Join-Path $tempDirectory "word") -Force | Out-Null

[System.IO.File]::WriteAllText((Join-Path $tempDirectory "[Content_Types].xml"), $contentTypes, [System.Text.Encoding]::UTF8)
[System.IO.File]::WriteAllText((Join-Path $tempDirectory "_rels\.rels"), $relationships, [System.Text.Encoding]::UTF8)
[System.IO.File]::WriteAllText((Join-Path $tempDirectory "word\document.xml"), $documentXml, [System.Text.Encoding]::UTF8)

if (Test-Path -LiteralPath $outputFullPath) {
    Remove-Item -LiteralPath $outputFullPath -Force
}

$archiveStream = [System.IO.File]::Open($outputFullPath, [System.IO.FileMode]::CreateNew)
$archive = New-Object System.IO.Compression.ZipArchive(
    $archiveStream,
    [System.IO.Compression.ZipArchiveMode]::Create,
    $false
)

foreach ($entryInfo in @(
    @{ Name = "[Content_Types].xml"; Path = (Join-Path $tempDirectory "[Content_Types].xml") },
    @{ Name = "_rels/.rels"; Path = (Join-Path $tempDirectory "_rels\.rels") },
    @{ Name = "word/document.xml"; Path = (Join-Path $tempDirectory "word\document.xml") }
)) {
    $entry = $archive.CreateEntry($entryInfo.Name)
    $entryStream = $entry.Open()
    $fileStream = [System.IO.File]::OpenRead($entryInfo.Path)
    $fileStream.CopyTo($entryStream)
    $fileStream.Dispose()
    $entryStream.Dispose()
}

$archive.Dispose()
$archiveStream.Dispose()
$resolvedTempDirectory = [System.IO.Path]::GetFullPath($tempDirectory)
$resolvedTempRoot = [System.IO.Path]::GetFullPath([System.IO.Path]::GetTempPath())
if (-not $resolvedTempDirectory.StartsWith($resolvedTempRoot, [System.StringComparison]::OrdinalIgnoreCase)) {
    throw "A pasta temporária não se encontra dentro da pasta temporária esperada."
}
Remove-Item -LiteralPath $resolvedTempDirectory -Recurse -Force

Write-Output $outputFullPath
