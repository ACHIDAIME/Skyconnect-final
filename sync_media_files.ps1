param([string]$FixturePath = "./fixtures/initial_data.json", [string]$MediaPath = "./media")

Write-Host "Synchronisation des fichiers media..." -ForegroundColor Green

$jsonContent = Get-Content -Path $FixturePath -Raw | ConvertFrom-Json
$mediaFields = @('image', 'avatar', 'file', 'document', 'photo')
$missing = 0; $created = 0

foreach ($item in $jsonContent) {
    foreach ($field in $mediaFields) {
        if ($item.fields.$field) {
            $filePath = $item.fields.$field
            $fullPath = Join-Path -Path $MediaPath -ChildPath $filePath
            $fullPath = $fullPath -replace '/', '\'
            
            if (-not (Test-Path $fullPath)) {
                Write-Host "Manquant: $filePath" -ForegroundColor Yellow
                $missing++
                
                $directory = Split-Path -Path $fullPath
                $filename = Split-Path -Path $fullPath -Leaf
                $nameWithoutExt = [System.IO.Path]::GetFileNameWithoutExtension($filename)
                $extension = [System.IO.Path]::GetExtension($filename)
                
                if (Test-Path $directory) {
                    $matches = @(Get-ChildItem -Path $directory -Filter "$nameWithoutExt*$extension" -Force)
                    
                    if ($matches.Count -gt 0) {
                        $sourceFile = $matches[0].FullName
                        Write-Host "  Trouvé: $($matches[0].Name) -> Copie..." -ForegroundColor Green
                        Copy-Item -Path $sourceFile -Destination $fullPath -Force
                        $created++
                    }
                }
            }
        }
    }
}

Write-Host "Résumé: $missing manquants, $created créés" -ForegroundColor Green
