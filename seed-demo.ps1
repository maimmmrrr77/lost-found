# =====================================================================
#  Nap bo du lieu kiem thu vao he thong Lost & Found AI
#  Chay tu thu muc goc du an, sau khi "docker compose up" da san sang.
#
#  Cach chay:  powershell -ExecutionPolicy Bypass -File seed-demo.ps1
# =====================================================================

$ErrorActionPreference = 'Stop'
$API = 'http://localhost:8080/api'

# Bao dam PowerShell gui va nhan UTF-8, tranh loi font tieng Viet
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
$PSDefaultParameterValues['Invoke-RestMethod:ContentType'] = 'application/json; charset=utf-8'

function Post-Json($path, $obj, $token) {
    $headers = @{}
    if ($token) { $headers['Authorization'] = "Bearer $token" }
    $json  = $obj | ConvertTo-Json -Depth 5 -Compress
    $bytes = [System.Text.Encoding]::UTF8.GetBytes($json)
    return Invoke-RestMethod -Uri "$API$path" -Method Post -Headers $headers `
           -ContentType 'application/json; charset=utf-8' -Body $bytes
}

function Ensure-User($fullName, $username, $email, $password) {
    try {
        Post-Json '/auth/register' @{
            full_name = $fullName; username = $username
            email = $email; password = $password
        } $null | Out-Null
        Write-Host "  [+] Da tao tai khoan $email"
    } catch {
        Write-Host "  [=] Tai khoan $email da ton tai, bo qua"
    }
    $r = Post-Json '/auth/login' @{ identity = $email; password = $password } $null
    return $r.data.token
}

Write-Host ""
Write-Host "=== BUOC 1: Tao hai tai khoan thu nghiem ===" -ForegroundColor Cyan
$tokenA = Ensure-User 'Nguyen Van An'  'nguyenvanan'  'an@example.com'  'MatKhau123'
$tokenB = Ensure-User 'Tran Thi Binh'  'tranthibinh'  'binh@example.com' 'MatKhau123'

Write-Host ""
Write-Host "=== BUOC 2: Tai khoan A dang 6 bai LOST ===" -ForegroundColor Cyan

$lost = @(
  @{ category_id=1; title='Mất iPhone 15 màu đen';        description='Máy có ốp lưng trong suốt, xước nhẹ ở góc phải'; color='Đen';  brand='Apple'; location='PTIT Hà Đông';        event_date='2026-08-20 08:30:00' }
  @{ category_id=2; title='Mất ví da màu nâu';            description='Bên trong có căn cước công dân và thẻ ngân hàng'; color='Nâu';  brand='';      location='Căng tin PTIT';        event_date='2026-08-20 11:15:00' }
  @{ category_id=3; title='Mất chùm chìa khóa xe máy';    description='Chùm chìa khóa Honda có móc treo hình con gấu nhỏ màu nâu'; color='Bạc'; brand='Honda'; location='Bãi gửi xe ký túc xá'; event_date='2026-08-19 17:40:00' }
  @{ category_id=4; title='Mất đồng hồ Casio đen';        description='Đồng hồ điện tử dây nhựa, mặt vuông'; color='Đen'; brand='Casio'; location='Sân bóng PTIT';       event_date='2026-08-18 16:00:00' }
  @{ category_id=5; title='Mất thẻ sinh viên';            description='Thẻ sinh viên tên Nguyễn Văn An, mã B22DCCN001'; color=''; brand=''; location='Thư viện PTIT';        event_date='2026-08-20 14:20:00' }
  @{ category_id=6; title='Mất laptop Dell XPS màu bạc';  description='Máy có dán sticker hình mèo ở mặt lưng'; color='Bạc'; brand='Dell'; location='Phòng học 2A15';      event_date='2026-08-17 09:00:00' }
)

foreach ($p in $lost) {
    $p['post_type'] = 'LOST'; $p['contact'] = '0900000001'; $p['reward'] = 0
    $r = Post-Json '/posts' $p $tokenA
    Write-Host ("  [+] LOST #{0}  {1}" -f $r.data.id, $p.title)
}

Write-Host ""
Write-Host "=== BUOC 3: Tai khoan B dang 8 bai FOUND (kich hoat so khop) ===" -ForegroundColor Cyan

$found = @(
  @{ category_id=1; title='Nhặt được iPhone 15 màu đen tại PTIT';        description='Điện thoại có ốp lưng trong suốt, góc phải bị xước nhẹ'; color='Đen';   brand='Apple';   location='PTIT Hà Đông';       event_date='2026-08-20 09:10:00' }
  @{ category_id=2; title='Nhặt được một chiếc ví màu nâu';              description='Trong ví có giấy tờ tùy thân và thẻ ATM'; color='Nâu';   brand='';        location='Khu căng tin';       event_date='2026-08-20 12:00:00' }
  @{ category_id=3; title='Nhặt được chìa khóa có móc gấu bông';         description='Chùm chìa khóa xe máy, móc treo hình chú gấu màu nâu'; color='Bạc'; brand='Honda'; location='Nhà xe ký túc xá'; event_date='2026-08-19 18:05:00' }
  @{ category_id=4; title='Nhặt được đồng hồ đeo tay Casio';             description='Đồng hồ điện tử màu đen, dây nhựa, mặt vuông'; color='Đen'; brand='Casio'; location='Sân bóng';          event_date='2026-08-18 17:30:00' }
  @{ category_id=5; title='Nhặt được thẻ sinh viên Học viện Bưu chính';  description='Thẻ mang tên Nguyễn Văn An, mã số B22DCCN001'; color=''; brand='';        location='Tầng 2 thư viện';    event_date='2026-08-20 15:00:00' }
  @{ category_id=1; title='Nhặt được Samsung Galaxy S24 màu trắng';      description='Máy còn mới, không ốp lưng'; color='Trắng'; brand='Samsung'; location='Cổng trường';    event_date='2026-08-20 10:00:00' }
  @{ category_id=2; title='Nhặt được ví vải màu đen';                    description='Ví nhỏ đựng tiền lẻ, không có giấy tờ'; color='Đen';  brand='';        location='Sân trường';         event_date='2026-08-19 13:25:00' }
  @{ category_id=4; title='Nhặt được đồng hồ Rolex mạ vàng';             description='Đồng hồ cơ dây kim loại, mặt tròn'; color='Vàng'; brand='Rolex';   location='Nhà gửi xe';         event_date='2026-08-18 08:45:00' }
)

foreach ($p in $found) {
    $p['post_type'] = 'FOUND'; $p['contact'] = '0900000002'; $p['reward'] = 0
    $r = Post-Json '/posts' $p $tokenB
    Write-Host ("  [+] FOUND #{0} {1}" -f $r.data.id, $p.title)
}

Write-Host ""
Write-Host "=== BUOC 4: Ket qua so khop AI ===" -ForegroundColor Cyan
$matchResult = Invoke-RestMethod -Uri "$API/matches/mine" -Headers @{ Authorization = "Bearer $tokenA" }

if (-not $matchResult.data -or $matchResult.data.Count -eq 0) {
    Write-Host "  Khong co cap nao vuot nguong. Hay giam AI_MATCH_THRESHOLD trong .env." -ForegroundColor Yellow
} else {
    Write-Host ("  Tim thay {0} cap:" -f $matchResult.data.Count) -ForegroundColor Green
    $matchResult.data | ForEach-Object {
        Write-Host ("   - {0,6:P1}  [{1}]  <->  [{2}]" -f `
            [double]$_.similarity_score, $_.lost_title, $_.found_title)
    }
}

Write-Host ""
Write-Host "Xong. Dang nhap bang an@example.com / MatKhau123 va mo muc 'Goi y AI'." -ForegroundColor Green
Write-Host ""
