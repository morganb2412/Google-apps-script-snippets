$ErrorActionPreference = 'Stop'
Add-Type -AssemblyName System.Drawing

$extensionRoot = (Resolve-Path (Join-Path $PSScriptRoot '..')).Path
$iconDirectory = Join-Path $extensionRoot 'public\icons'
New-Item -ItemType Directory -Path $iconDirectory -Force | Out-Null

foreach ($size in @(16, 32, 48, 128)) {
    $bitmap = New-Object System.Drawing.Bitmap($size, $size)
    $graphics = [System.Drawing.Graphics]::FromImage($bitmap)
    try {
        $graphics.SmoothingMode = [System.Drawing.Drawing2D.SmoothingMode]::AntiAlias
        $graphics.Clear([System.Drawing.Color]::FromArgb(17, 25, 37))
        $inset = [Math]::Max(1, [Math]::Round($size * 0.08))
        $accentBrush = New-Object System.Drawing.SolidBrush([System.Drawing.Color]::FromArgb(102, 173, 255))
        $graphics.FillRectangle($accentBrush, $inset, $inset, $size - (2 * $inset), $size - (2 * $inset))
        $fontSize = [Math]::Max(6, [Math]::Round($size * 0.34))
        $font = New-Object System.Drawing.Font('Arial', $fontSize, [System.Drawing.FontStyle]::Bold, [System.Drawing.GraphicsUnit]::Pixel)
        $textBrush = New-Object System.Drawing.SolidBrush([System.Drawing.Color]::FromArgb(7, 17, 29))
        $format = New-Object System.Drawing.StringFormat
        $format.Alignment = [System.Drawing.StringAlignment]::Center
        $format.LineAlignment = [System.Drawing.StringAlignment]::Center
        $graphics.DrawString('DB', $font, $textBrush, (New-Object System.Drawing.RectangleF(0, 0, $size, $size)), $format)
        $bitmap.Save((Join-Path $iconDirectory "icon$size.png"), [System.Drawing.Imaging.ImageFormat]::Png)
    } finally {
        $graphics.Dispose()
        $bitmap.Dispose()
        if ($accentBrush) { $accentBrush.Dispose() }
        if ($textBrush) { $textBrush.Dispose() }
        if ($font) { $font.Dispose() }
        if ($format) { $format.Dispose() }
    }
}
