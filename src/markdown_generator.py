"""
Markdown 生成模块
负责将新闻数据生成为 Markdown 格式文件
"""

import os
from datetime import datetime
from typing import List, Dict, Any
from loguru import logger


class MarkdownGenerator:
    """Markdown 文件生成器"""
    
    def __init__(self, output_dir: str = 'output'):
        self.output_dir = output_dir
        logger.info(f"MarkdownGenerator initialized with output_dir: {output_dir}")
    
    def generate_daily_digest(
        self,
        categorized_news: Dict[str, List[Dict[str, Any]]],
        date: str = None
    ) -> str:
        """
        生成每日新闻摘要 Markdown 文件
        
        Args:
            categorized_news: 按分类组织的新闻数据
            date: 日期字符串，默认为今天
            
        Returns:
            生成的文件路径
        """
        if date is None:
            date = datetime.now().strftime('%Y-%m-%d')
        
        # 创建日期目录
        date_dir = os.path.join(self.output_dir, date)
        os.makedirs(date_dir, exist_ok=True)
        
        # 生成 Markdown 内容
        markdown_content = self._build_markdown(categorized_news, date)
        
        # 写入文件
        output_file = os.path.join(date_dir, 'news_digest.md')
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(markdown_content)
        
        logger.success(f"Generated daily digest: {output_file}")
        return output_file
    
    def _build_markdown(self, categorized_news: Dict[str, List[Dict[str, Any]]], date: str) -> str:
        """
        构建 Markdown 内容
        
        Args:
            categorized_news: 按分类组织的新闻数据
            date: 日期字符串
            
        Returns:
            Markdown 格式的字符串
        """
        lines = []
        
        # 标题
        lines.append(f"# 每日新闻摘要 - {date}\n")
        lines.append(f"**生成时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        lines.append("---\n")
        
        # 目录
        lines.append("## 📑 目录\n")
        for category_name in categorized_news.keys():
            lines.append(f"- [{category_name}](#{self._slugify(category_name)})")
        lines.append("\n---\n")
        
        # 各分类内容
        for category_name, news_list in categorized_news.items():
            lines.append(f"## {category_name}\n")
            
            # 按新闻源分组
            sources = {}
            for news in news_list:
                source_name = news.get('source_name', '未知来源')
                if source_name not in sources:
                    sources[source_name] = []
                sources[source_name].append(news)
            
            # 输出每个新闻源
            for source_name, articles in sources.items():
                lines.append(f"### 📰 {source_name}\n")
                lines.append(f"**文章数量**: {len(articles)}\n")
                
                for idx, article in enumerate(articles, 1):
                    lines.append(f"#### {idx}. {article.get('title', '无标题')}\n")
                    
                    # 元信息
                    if article.get('author'):
                        lines.append(f"**作者**: {article['author']}  ")
                    if article.get('date'):
                        lines.append(f"**发布时间**: {article['date']}  ")
                    if article.get('url'):
                        lines.append(f"**原文链接**: [{article['url']}]({article['url']})\n")
                    
                    # 摘要
                    if article.get('excerpt'):
                        lines.append(f"**摘要**: {article['excerpt']}\n")
                    
                    # 正文内容
                    if article.get('content'):
                        lines.append("**正文内容**:\n")
                        lines.append(f"{article['content']}\n")
                    else:
                        lines.append("*（未能提取正文内容）*\n")
                    
                    lines.append("---\n")
                
                lines.append("\n")
            
            lines.append("\n")
        
        # 页脚
        lines.append("---\n")
        lines.append(f"*本文档由 News2Context 自动生成于 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*\n")
        
        return '\n'.join(lines)
    
    def _slugify(self, text: str) -> str:
        """
        将文本转换为适合作为锚点的格式
        
        Args:
            text: 原始文本
            
        Returns:
            处理后的文本
        """
        # 简单处理：移除空格和特殊字符
        import re
        text = re.sub(r'[^\w\s-]', '', text)
        text = re.sub(r'[\s_-]+', '-', text)
        return text.lower()


def main():
    """测试函数"""
    generator = MarkdownGenerator()
    
    # 测试数据
    test_data = {
        "财经金融": [
            {
                "title": "华尔街见闻测试文章",
                "source_name": "华尔街见闻-日排行",
                "url": "https://example.com/article1",
                "excerpt": "这是一篇测试文章的摘要",
                "content": "这是正文内容，包含详细的财经分析...",
                "author": "张三",
                "date": "2025-11-25"
            }
        ],
        "科技互联网": [
            {
                "title": "36氪测试文章",
                "source_name": "36氪-24小时热榜",
                "url": "https://example.com/article2",
                "excerpt": "科技新闻摘要",
                "content": "科技新闻正文内容...",
            }
        ]
    }
    
    output_file = generator.generate_daily_digest(test_data)
    print(f"生成的文件: {output_file}")


if __name__ == '__main__':
    main()
