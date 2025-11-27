"""
Markdown 解析器
解析新闻摘要 Markdown 文件，提取文章结构
"""

import re
from typing import List, Dict, Any
from dataclasses import dataclass
from loguru import logger


@dataclass
class Article:
    """新闻文章数据结构"""
    title: str              # 新闻标题
    content: str            # 正文内容
    category: str           # 分类（财经、科技等）
    source: str             # 来源（华尔街见闻等）
    url: str                # 原文链接
    char_count: int         # 字符数


class MarkdownParser:
    """Markdown 解析器"""
    
    def __init__(self):
        """初始化解析器"""
        # 匹配 #### 标题（新闻标题）
        self.article_pattern = re.compile(r'^####\s+(\d+)\.\s+(.+)$', re.MULTILINE)
        # 匹配 ### 标题（新闻源）
        self.source_pattern = re.compile(r'^###\s+📰\s+(.+)$', re.MULTILINE)
        # 匹配 ## 标题（分类）
        self.category_pattern = re.compile(r'^##\s+(.+)$', re.MULTILINE)
        # 匹配链接
        self.url_pattern = re.compile(r'\*\*原文链接\*\*:\s+\[(.+?)\]\((.+?)\)')
    
    def parse_digest(self, markdown_path: str) -> List[Article]:
        """
        解析新闻摘要 Markdown 文件
        
        Args:
            markdown_path: Markdown 文件路径
            
        Returns:
            文章列表
        """
        logger.info(f"开始解析 Markdown 文件: {markdown_path}")
        
        with open(markdown_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        articles = self.extract_articles(content)
        
        logger.success(f"解析完成: 提取 {len(articles)} 篇文章")
        return articles
    
    def extract_articles(self, content: str) -> List[Article]:
        """
        提取所有新闻文章
        
        Args:
            content: Markdown 内容
            
        Returns:
            文章列表
        """
        articles = []
        
        # 按 ## 分类分割
        category_sections = re.split(r'^## ', content, flags=re.MULTILINE)[1:]
        
        for category_section in category_sections:
            lines = category_section.split('\n')
            category = lines[0].strip()
            
            # 跳过目录和统计部分
            if category in ['📑 目录', '📊 采集统计']:
                continue
            
            # 按 ### 新闻源分割
            source_sections = re.split(r'^### ', category_section, flags=re.MULTILINE)[1:]
            
            for source_section in source_sections:
                source_lines = source_section.split('\n')
                source_name = source_lines[0].replace('📰 ', '').strip()
                
                # 按 #### 文章标题分割
                article_sections = re.split(r'^#### ', source_section, flags=re.MULTILINE)[1:]
                
                for article_section in article_sections:
                    article = self._parse_article(
                        article_section,
                        category=category,
                        source=source_name
                    )
                    if article:
                        articles.append(article)
        
        return articles
    
    def _parse_article(
        self,
        article_text: str,
        category: str,
        source: str
    ) -> Article:
        """
        解析单篇文章
        
        Args:
            article_text: 文章文本
            category: 分类
            source: 来源
            
        Returns:
            Article 对象或 None
        """
        lines = article_text.split('\n')
        
        # 提取标题（第一行）
        title_line = lines[0].strip()
        # 移除序号（如 "1. "）
        title_match = re.match(r'^\d+\.\s+(.+)$', title_line)
        if title_match:
            title = title_match.group(1)
        else:
            title = title_line
        
        # 提取 URL
        url = ""
        url_match = self.url_pattern.search(article_text)
        if url_match:
            url = url_match.group(2)
        
        # 提取正文内容
        content_parts = []
        in_content = False
        
        for line in lines[1:]:
            # 跳过空行和分隔符
            if not line.strip() or line.strip() == '---':
                continue
            
            # 跳过链接行
            if '**原文链接**' in line:
                continue
            
            # 开始收集正文
            if '**正文内容**' in line or '**摘要**' in line:
                in_content = True
                continue
            
            if in_content:
                # 遇到下一个标题或分隔符，停止
                if line.startswith('#') or line.strip() == '---':
                    break
                content_parts.append(line)
        
        content = '\n'.join(content_parts).strip()
        
        # 如果没有内容，跳过
        if not content:
            return None
        
        return Article(
            title=title,
            content=content,
            category=category,
            source=source,
            url=url,
            char_count=len(title) + len(content)
        )
