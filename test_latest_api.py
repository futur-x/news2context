"""测试最新 API"""
import asyncio
from src.engines.tophub_engine import TopHubEngine
from src.utils.config import get_config

async def test():
    config = get_config()
    engine = TopHubEngine(config.config)
    
    # 测试获取微博热搜
    result = await engine.fetch_news('KqndgxeLl9')
    print(f'获取到 {len(result)} 条新闻')
    if result:
        print(f'第一条: {result[0]["title"]}')

if __name__ == "__main__":
    asyncio.run(test())
