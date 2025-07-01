#!/usr/bin/env python3
"""
网络连接测试工具
用于诊断SSL连接和网络问题
"""

import asyncio
import ssl
import socket
import httpx
from urllib.parse import urlparse
import sys


async def test_basic_connectivity():
    """测试基本网络连接"""
    print("=== 基本网络连接测试 ===")
    
    test_hosts = [
        ("www.xiaohongshu.com", 443),
        ("www.baidu.com", 443),
        ("www.google.com", 443),
    ]
    
    for host, port in test_hosts:
        try:
            # 测试TCP连接
            future = asyncio.open_connection(host, port)
            reader, writer = await asyncio.wait_for(future, timeout=10)
            writer.close()
            await writer.wait_closed()
            print(f"✓ {host}:{port} - TCP连接成功")
        except asyncio.TimeoutError:
            print(f"✗ {host}:{port} - 连接超时")
        except Exception as e:
            print(f"✗ {host}:{port} - 连接失败: {e}")


async def test_ssl_connectivity():
    """测试SSL连接"""
    print("\n=== SSL连接测试 ===")
    
    test_urls = [
        "https://www.xiaohongshu.com",
        "https://www.baidu.com",
        "https://httpbin.org/get",
    ]
    
    print("使用httpx测试SSL连接...")
    
    for url in test_urls:
        print(f"\n测试URL: {url}")
        
        # 测试默认SSL配置
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(url)
                print(f"  ✓ 默认SSL配置: {response.status_code}")
        except httpx.SSLError as e:
            print(f"  ✗ 默认SSL配置: SSL错误 - {e}")
        except httpx.ConnectError as e:
            print(f"  ✗ 默认SSL配置: 连接错误 - {e}")
        except httpx.TimeoutException:
            print(f"  ✗ 默认SSL配置: 请求超时")
        except Exception as e:
            print(f"  ✗ 默认SSL配置: 其他错误 - {e}")
        
        # 测试禁用SSL验证
        try:
            async with httpx.AsyncClient(verify=False, timeout=10.0) as client:
                response = await client.get(url)
                print(f"  ✓ 禁用SSL验证: {response.status_code}")
        except httpx.ConnectError as e:
            print(f"  ✗ 禁用SSL验证: 连接错误 - {e}")
        except httpx.TimeoutException:
            print(f"  ✗ 禁用SSL验证: 请求超时")
        except Exception as e:
            print(f"  ✗ 禁用SSL验证: 其他错误 - {e}")


async def test_httpx_connectivity():
    """测试httpx连接"""
    print("\n=== HTTPX连接测试 ===")
    
    test_urls = [
        "https://www.xiaohongshu.com",
        "https://www.baidu.com",
        "https://httpbin.org/get",
    ]
    
    # 测试不同的客户端配置
    configs = [
        ("默认配置", {}),
        ("禁用SSL验证", {"verify": False}),
        ("增加超时", {"timeout": 30.0}),
        ("禁用SSL验证+增加超时", {"verify": False, "timeout": 30.0}),
    ]
    
    for url in test_urls:
        print(f"\n测试URL: {url}")
        
        for config_name, config in configs:
            try:
                async with httpx.AsyncClient(**config) as client:
                    response = await client.get(url)
                    print(f"  ✓ {config_name}: {response.status_code}")
                    
            except httpx.TimeoutException:
                print(f"  ✗ {config_name}: 请求超时")
            except httpx.SSLError as e:
                print(f"  ✗ {config_name}: SSL错误 - {e}")
            except httpx.ConnectError as e:
                print(f"  ✗ {config_name}: 连接错误 - {e}")
            except Exception as e:
                print(f"  ✗ {config_name}: 其他错误 - {e}")


def test_dns_resolution():
    """测试DNS解析"""
    print("\n=== DNS解析测试 ===")
    
    test_hosts = [
        "www.xiaohongshu.com",
        "www.baidu.com",
        "www.google.com",
        "httpbin.org",
    ]
    
    for host in test_hosts:
        try:
            ip_addresses = socket.gethostbyname_ex(host)[2]
            print(f"✓ {host} -> {', '.join(ip_addresses)}")
        except socket.gaierror as e:
            print(f"✗ {host} - DNS解析失败: {e}")
        except Exception as e:
            print(f"✗ {host} - 解析错误: {e}")


def test_proxy_settings():
    """检查代理设置"""
    print("\n=== 代理设置检查 ===")
    
    import os
    proxy_vars = ['HTTP_PROXY', 'HTTPS_PROXY', 'http_proxy', 'https_proxy', 'ALL_PROXY']
    
    found_proxy = False
    for var in proxy_vars:
        value = os.environ.get(var)
        if value:
            print(f"发现代理设置: {var} = {value}")
            found_proxy = True
    
    if not found_proxy:
        print("未发现系统代理设置")


def check_ssl_version():
    """检查SSL版本"""
    print("\n=== SSL版本信息 ===")
    print(f"SSL版本: {ssl.OPENSSL_VERSION}")
    print(f"支持的协议: {', '.join(ssl._PROTOCOL_NAMES.values())}")


async def main():
    """主函数"""
    print("MediaCrawler 网络连接诊断工具")
    print("=" * 50)
    
    # 基本信息
    print(f"Python版本: {sys.version}")
    check_ssl_version()
    test_proxy_settings()
    test_dns_resolution()
    
    # 连接测试
    await test_basic_connectivity()
    await test_ssl_connectivity()
    await test_httpx_connectivity()
    
    print("\n=== 测试完成 ===")
    print("如果大部分连接都失败，可能的解决方案：")
    print("1. 检查网络连接和防火墙设置")
    print("2. 尝试使用代理服务器")
    print("3. 暂时禁用SSL证书验证（不推荐，仅用于测试）")
    print("4. 检查DNS设置，尝试更换DNS服务器")


if __name__ == "__main__":
    asyncio.run(main())
