# 猎鹰招聘系统 - Nginx 部署验证脚本 (PowerShell)
# 用于验证生产环境部署是否正确

param(
    [string]$BaseUrl = "http://localhost"
)

Write-Host "==========================================" -ForegroundColor Cyan
Write-Host "  猎鹰招聘系统 - 部署验证" -ForegroundColor Cyan
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "测试地址: $BaseUrl" -ForegroundColor Yellow
Write-Host ""

# 计数器
$Pass = 0
$Fail = 0

# 测试函数
function Test-Endpoint {
    param(
        [string]$Name,
        [string]$Url,
        [int]$ExpectedStatus = 200
    )
    
    Write-Host -NoNewline "测试 $Name ... "
    
    try {
        $response = Invoke-WebRequest -Uri $Url -Method Get -UseBasicParsing -TimeoutSec 5
        $statusCode = $response.StatusCode
    } catch {
        if ($_.Exception.Response) {
            $statusCode = $_.Exception.Response.StatusCode.value__
        } else {
            $statusCode = 0
        }
    }
    
    if ($statusCode -eq $ExpectedStatus) {
        Write-Host "✓ PASS (HTTP $statusCode)" -ForegroundColor Green
        $script:Pass++
        return $true
    } else {
        Write-Host "✗ FAIL (期望: HTTP $ExpectedStatus, 实际: HTTP $statusCode)" -ForegroundColor Red
        $script:Fail++
        return $false
    }
}

# 1. 测试前端页面
Test-Endpoint -Name "前端页面" -Url "$BaseUrl/" -ExpectedStatus 200

# 2. 测试后端健康检查
Test-Endpoint -Name "健康检查" -Url "$BaseUrl/api/health" -ExpectedStatus 200

# 3. 测试 API 文档（如果启用）
Write-Host -NoNewline "测试 API 文档 ... "
try {
    $response = Invoke-WebRequest -Uri "$BaseUrl/api/docs" -Method Get -UseBasicParsing -TimeoutSec 5
    $statusCode = $response.StatusCode
    if ($statusCode -eq 200 -or $statusCode -eq 401) {
        Write-Host "✓ PASS (HTTP $statusCode)" -ForegroundColor Green
        $script:Pass++
    } else {
        Write-Host "⚠ SKIP (HTTP $statusCode - 可能已禁用)" -ForegroundColor Yellow
    }
} catch {
    if ($_.Exception.Response) {
        $statusCode = $_.Exception.Response.StatusCode.value__
        Write-Host "⚠ SKIP (HTTP $statusCode - 可能已禁用)" -ForegroundColor Yellow
    } else {
        Write-Host "⚠ SKIP (无法访问)" -ForegroundColor Yellow
    }
}

# 4. 测试 CORS 头
Write-Host -NoNewline "测试 CORS 配置 ... "
try {
    $headers = @{ "Origin" = "http://test.com" }
    $response = Invoke-WebRequest -Uri "$BaseUrl/api/health" -Method Get -Headers $headers -UseBasicParsing -TimeoutSec 5
    if ($response.Headers.ContainsKey("Access-Control-Allow-Origin")) {
        Write-Host "✓ PASS (CORS 头已配置)" -ForegroundColor Green
        $script:Pass++
    } else {
        Write-Host "⚠ INFO (通过 Nginx 统一入口，无需 CORS)" -ForegroundColor Yellow
    }
} catch {
    Write-Host "⚠ INFO (通过 Nginx 统一入口，无需 CORS)" -ForegroundColor Yellow
}

# 5. 测试容器状态
Write-Host ""
Write-Host "检查容器状态..." -ForegroundColor Cyan

if (Get-Command docker -ErrorAction SilentlyContinue) {
    $containers = @("falcon-nginx", "falcon-backend", "falcon-frontend", "falcon-postgres", "falcon-redis")
    
    foreach ($container in $containers) {
        try {
            $result = docker ps --format "{{.Names}}" | Select-String "^${container}$"
            if ($result) {
                Write-Host "  ✓ $container 运行中" -ForegroundColor Green
                $script:Pass++
            } else {
                Write-Host "  ✗ $container 未运行" -ForegroundColor Red
                $script:Fail++
            }
        } catch {
            Write-Host "  ✗ $container 检查失败" -ForegroundColor Red
            $script:Fail++
        }
    }
} else {
    Write-Host "  ⚠ Docker 未安装，跳过容器检查" -ForegroundColor Yellow
}

# 总结
Write-Host ""
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host "  测试结果汇总" -ForegroundColor Cyan
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host "通过: $Pass" -ForegroundColor Green
Write-Host "失败: $Fail" -ForegroundColor Red
Write-Host ""

if ($Fail -eq 0) {
    Write-Host "✓ 所有测试通过！部署成功！" -ForegroundColor Green
    exit 0
} else {
    Write-Host "✗ 存在失败的测试，请检查部署配置" -ForegroundColor Red
    exit 1
}
