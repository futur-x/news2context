"""
测试 GBK 编码支持和 Economist 问题诊断
"""
import asyncio
import aiohttp
from src.extractor import ContentExtractor

async def test_gbk_encoding():
    """测试 GBK 编码网站"""
    print("=" * 60)
    print("测试 1: GBK 编码网站 (stocknews.scol.com.cn)")
    print("=" * 60)
    
    extractor = ContentExtractor()
    test_url = "https://stocknews.scol.com.cn/shtml/jrtzb/20251115/142403.shtml"
    
    async with aiohttp.ClientSession() as session:
        result = await extractor.extract_from_url(test_url, session)
        
        if result:
            print(f"✅ 成功提取")
            print(f"标题: {result['title']}")
            print(f"内容长度: {len(result['content'])} 字符")
            print(f"内容预览: {result['content'][:200]}...")
        else:
            print("❌ 提取失败")

async def test_economist():
    """测试 Economist 网站"""
    print("\n" + "=" * 60)
    print("测试 2: Economist 网站")
    print("=" * 60)
    
    extractor = ContentExtractor(timeout=15)  # 15秒超时
    test_url = "https://www.economist.com/special-report/2025/11/10/acknowledgments"
    
    print(f"URL: {test_url}")
    print(f"超时设置: {extractor.timeout}秒")
    
    async with aiohttp.ClientSession() as session:
        import time
        start = time.time()
        
        result = await extractor.extract_from_url(test_url, session)
        
        elapsed = time.time() - start
        print(f"耗时: {elapsed:.2f}秒")
        
        if result:
            print(f"✅ 成功提取")
            print(f"标题: {result['title']}")
            print(f"内容长度: {len(result['content'])} 字符")
        else:
            print("❌ 提取失败（可能是超时或反爬虫）")

async def diagnose_economist():
    """诊断 Economist 问题"""
    print("\n" + "=" * 60)
    print("诊断 3: Economist 访问问题")
    print("=" * 60)
    
    test_url = "https://www.economist.com/special-report/2025/11/10/acknowledgments"
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
    }
    
    try:
        async with aiohttp.ClientSession() as session:
            print("正在访问 Economist...")
            async with session.get(test_url, headers=headers, timeout=15) as response:
                print(f"HTTP 状态码: {response.status}")
                print(f"Content-Type: {response.headers.get('Content-Type')}")
                print(f"Content-Length: {response.headers.get('Content-Length')}")
                
                html = await response.text()
                print(f"HTML 长度: {len(html)} 字符")
                
                # 检查是否有反爬虫机制
                if 'cloudflare' in html.lower():
                    print("⚠️  检测到 Cloudflare 防护")
                if 'captcha' in html.lower():
                    print("⚠️  检测到 CAPTCHA")
                if len(html) < 1000:
                    print("⚠️  返回内容过短，可能被拦截")
                    print(f"内容预览: {html[:500]}")
                
    except asyncio.TimeoutError:
        print("❌ 连接超时")
    except Exception as e:
        print(f"❌ 错误: {str(e)}")

async def main():
    print("\n🔍 开始诊断测试...\n")
    
    # 测试 1: GBK 编码
    await test_gbk_encoding()
    
    # 测试 2: Economist 提取
    await test_economist()
    
    # 测试 3: Economist 诊断
    await diagnose_economist()
    
    print("\n" + "=" * 60)
    print("📊 总结")
    print("=" * 60)
    print("""
Economist 问题原因：
1. **反爬虫机制** - 可能使用 Cloudflare 或其他防护
2. **动态加载** - 内容可能通过 JavaScript 加载
3. **地理限制** - 可能有地区访问限制
4. **付费墙** - 部分内容需要订阅

建议解决方案：
- 跳过 Economist 等难以提取的网站
- 或使用浏览器自动化工具（Playwright/Selenium）
- 或添加到黑名单，不采集此类源
    """)

if __name__ == "__main__":
    asyncio.run(main())
