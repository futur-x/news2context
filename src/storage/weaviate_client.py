"""
Weaviate Collection 管理器
负责 Weaviate Collection 的创建、删除和管理
"""

import weaviate
from typing import Dict, Any, List, Optional, Set
from loguru import logger


class CollectionManager:
    """Weaviate Collection 管理器"""
    
    # NewsArticle Schema 定义
    NEWS_ARTICLE_SCHEMA = {
        "class": "NewsArticle",
        "description": "新闻文章",
        "vectorizer": "text2vec-openai",
        "moduleConfig": {
            "text2vec-openai": {
                "model": "text-embedding-3-large",
                "type": "text",
                "baseURL": "https://litellm.futurx.cc"
            }
        },
        "properties": [
            {
                "name": "task_name",
                "dataType": ["string"],
                "description": "所属任务名称",
                "moduleConfig": {
                    "text2vec-openai": {
                        "skip": True
                    }
                }
            },
            {
                "name": "title",
                "dataType": ["text"],
                "description": "标题"
            },
            {
                "name": "content",
                "dataType": ["text"],
                "description": "正文内容"
            },
            {
                "name": "url",
                "dataType": ["string"],
                "description": "原文链接",
                "moduleConfig": {
                    "text2vec-openai": {
                        "skip": True
                    }
                }
            },
            {
                "name": "source_name",
                "dataType": ["string"],
                "description": "新闻源名称"
            },
            {
                "name": "source_hashid",
                "dataType": ["string"],
                "description": "新闻源 hashid",
                "moduleConfig": {
                    "text2vec-openai": {
                        "skip": True
                    }
                }
            },
            {
                "name": "published_at",
                "dataType": ["date"],
                "description": "发布时间"
            },
            {
                "name": "fetched_at",
                "dataType": ["date"],
                "description": "抓取时间"
            },
            {
                "name": "category",
                "dataType": ["string"],
                "description": "分类"
            },
            {
                "name": "excerpt",
                "dataType": ["text"],
                "description": "摘要"
            }
        ]
    }
    
    # NewsChunk Schema 定义（单篇新闻智能切割）
    NEWS_CHUNK_SCHEMA = {
        "class": "NewsChunk",
        "description": "新闻 Chunk（单篇新闻智能切割，支持超长文章）",
        "vectorizer": "text2vec-openai",
        "moduleConfig": {
            "text2vec-openai": {
                "model": "text-embedding-3-large",
                "type": "text",
                "baseURL": "https://litellm.futurx.cc"
            }
        },
        "properties": [
            {
                "name": "article_id",
                "dataType": ["string"],
                "description": "文章唯一标识（用于关联同一篇文章的多个 chunks）",
                "moduleConfig": {
                    "text2vec-openai": {
                        "skip": True
                    }
                }
            },
            {
                "name": "chunk_index",
                "dataType": ["int"],
                "description": "当前 chunk 索引（从 0 开始）",
                "moduleConfig": {
                    "text2vec-openai": {
                        "skip": True
                    }
                }
            },
            {
                "name": "total_chunks",
                "dataType": ["int"],
                "description": "该文章总共的 chunks 数量",
                "moduleConfig": {
                    "text2vec-openai": {
                        "skip": True
                    }
                }
            },
            {
                "name": "title",
                "dataType": ["text"],
                "description": "文章标题"
            },
            {
                "name": "content",
                "dataType": ["text"],
                "description": "Chunk 内容（包含标题和索引信息）"
            },
            {
                "name": "url",
                "dataType": ["string"],
                "description": "原文链接",
                "moduleConfig": {
                    "text2vec-openai": {
                        "skip": True
                    }
                }
            },
            {
                "name": "source_name",
                "dataType": ["string"],
                "description": "新闻源名称"
            },
            {
                "name": "source_hashid",
                "dataType": ["string"],
                "description": "新闻源 hashid",
                "moduleConfig": {
                    "text2vec-openai": {
                        "skip": True
                    }
                }
            },
            {
                "name": "category",
                "dataType": ["string"],
                "description": "分类"
            },
            {
                "name": "published_at",
                "dataType": ["date"],
                "description": "发布时间"
            },
            {
                "name": "fetched_at",
                "dataType": ["date"],
                "description": "抓取时间"
            },
            {
                "name": "task_name",
                "dataType": ["string"],
                "description": "所属任务名称",
                "moduleConfig": {
                    "text2vec-openai": {
                        "skip": True
                    }
                }
            },
            {
                "name": "excerpt",
                "dataType": ["text"],
                "description": "摘要"
            }
        ]
    }
    
    
    def __init__(self, weaviate_url: str, api_key: Optional[str] = None, additional_headers: Optional[Dict[str, str]] = None, embedding_config: Optional[Dict[str, Any]] = None):
        """
        初始化 Collection 管理器
        
        Args:
            weaviate_url: Weaviate 服务地址
            api_key: API Key（可选）
            additional_headers: 额外请求头（如 X-OpenAI-Api-Key）
            embedding_config: Embedding 模型配置（包含 model, base_url 等）
        """
        self.weaviate_url = weaviate_url
        self.api_key = api_key
        self.embedding_config = embedding_config or {}
        
        # 动态更新 NEWS_CHUNK_SCHEMA 的 embedding 模型配置
        if self.embedding_config:
            embedding_model = self.embedding_config.get('model', 'text-embedding-3-small')
            embedding_base_url = self.embedding_config.get('base_url', 'https://litellm.futurx.cc')
            
            # 更新 schema（创建副本以避免修改类变量）
            self.NEWS_CHUNK_SCHEMA = self.NEWS_CHUNK_SCHEMA.copy()
            self.NEWS_CHUNK_SCHEMA['moduleConfig'] = {
                "text2vec-openai": {
                    "model": embedding_model,
                    "type": "text",
                    "baseURL": embedding_base_url
                }
            }
            logger.info(f"使用 Embedding 模型: {embedding_model}")
        
        # 创建客户端（增加启动超时时间）
        if api_key:
            auth_config = weaviate.AuthApiKey(api_key=api_key)
            self.client = weaviate.Client(
                url=weaviate_url,
                auth_client_secret=auth_config,
                startup_period=30,  # 增加启动超时到 30 秒
                additional_headers=additional_headers
            )
        else:
            self.client = weaviate.Client(
                url=weaviate_url,
                startup_period=30,  # 增加启动超时到 30 秒
                additional_headers=additional_headers
            )
        
        # 测试连接
        if not self.client.is_ready():
            raise ConnectionError(f"无法连接到 Weaviate: {weaviate_url}")
        
        logger.info(f"Weaviate 客户端已连接: {weaviate_url}")
    
    def _format_class_name(self, name: str) -> str:
        """
        确保 Collection 名称符合 Weaviate 规范（首字母大写）
        如果名称包含非 ASCII 字符（如中文），则使用 MD5 哈希生成合法名称
        
        Args:
            name: 原始名称
            
        Returns:
            格式化后的名称
        """
        if not name:
            raise ValueError("Collection 名称不能为空")
            
        # 移除不支持的字符（Weaviate 只允许字母、数字和下划线）
        import re
        import hashlib
        
        # 尝试保留原始英文名称
        clean_name = re.sub(r'[^a-zA-Z0-9_]', '', name)
        
        # 如果清理后为空（例如全是中文），或者长度太短，使用 MD5
        if not clean_name or len(clean_name) < 2:
            # 使用 MD5 生成唯一标识
            hash_object = hashlib.md5(name.encode())
            hash_hex = hash_object.hexdigest()
            # 添加前缀确保首字母大写
            return f"Class_{hash_hex}"
            
        # 如果以数字或下划线开头，添加前缀
        if not clean_name[0].isalpha():
            clean_name = f"Class_{clean_name}"
            
        # 确保首字母大写
        return clean_name[0].upper() + clean_name[1:]

    def create_collection(self, collection_name: str, schema: Dict[str, Any] = None) -> bool:
        """
        创建 Collection
        
        Args:
            collection_name: Collection 名称
            schema: Schema 定义 (默认使用 NEWS_ARTICLE_SCHEMA)
            
        Returns:
            是否成功创建
        """
        collection_name = self._format_class_name(collection_name)
        
        # 检查是否已存在
        if self.collection_exists(collection_name):
            # logger.warning(f"Collection 已存在: {collection_name}")
            return False
        
        # 创建 Schema（使用 Collection 名称）
        if schema is None:
            schema = self.NEWS_ARTICLE_SCHEMA.copy()
        else:
            schema = schema.copy()
            
        schema['class'] = collection_name
        
        try:
            self.client.schema.create_class(schema)
            logger.success(f"Collection 已创建: {collection_name}")
            return True
        except Exception as e:
            logger.error(f"创建 Collection 失败: {str(e)}")
            return False
    
    def delete_collection(self, collection_name: str) -> bool:
        """
        删除 Collection
        
        Args:
            collection_name: Collection 名称
            
        Returns:
            是否成功删除
        """
        collection_name = self._format_class_name(collection_name)
        
        if not self.collection_exists(collection_name):
            logger.warning(f"Collection 不存在: {collection_name}")
            return False
        
        try:
            self.client.schema.delete_class(collection_name)
            logger.success(f"Collection 已删除: {collection_name}")
            return True
        except Exception as e:
            logger.error(f"删除 Collection 失败: {str(e)}")
            return False
    
    def collection_exists(self, collection_name: str) -> bool:
        """
        检查 Collection 是否存在
        
        Args:
            collection_name: Collection 名称
            
        Returns:
            是否存在
        """
        collection_name = self._format_class_name(collection_name)
        
        try:
            schema = self.client.schema.get()
            classes = schema.get('classes', [])
            return any(c['class'] == collection_name for c in classes)
        except Exception as e:
            logger.error(f"检查 Collection 失败: {str(e)}")
            return False
    
    def list_collections(self) -> List[str]:
        """
        列出所有 Collection
        
        Returns:
            Collection 名称列表
        """
        try:
            schema = self.client.schema.get()
            classes = schema.get('classes', [])
            return [c['class'] for c in classes]
        except Exception as e:
            logger.error(f"列出 Collection 失败: {str(e)}")
            return []
    
    def get_collection_stats(self, collection_name: str) -> Dict[str, Any]:
        """
        获取 Collection 统计信息
        
        Args:
            collection_name: Collection 名称
            
        Returns:
            统计信息字典
        """
        collection_name = self._format_class_name(collection_name)
        
        if not self.collection_exists(collection_name):
            return {}
        
        try:
            # 获取对象数量
            result = (
                self.client.query
                .aggregate(collection_name)
                .with_meta_count()
                .do()
            )
            
            count = result['data']['Aggregate'][collection_name][0]['meta']['count']
            
            return {
                'collection': collection_name,
                'total_objects': count
            }
        except Exception as e:
            logger.error(f"获取统计信息失败: {str(e)}")
            return {}
    
    def insert_news(
        self,
        collection_name: str,
        news_data: Dict[str, Any]
    ) -> Optional[str]:
        """
        插入单条新闻
        
        Args:
            collection_name: Collection 名称
            news_data: 新闻数据
            
        Returns:
            对象 UUID，失败返回 None
        """
        collection_name = self._format_class_name(collection_name)
        
        if not self.collection_exists(collection_name):
            logger.error(f"Collection 不存在: {collection_name}")
            return None
        
        try:
            uuid = self.client.data_object.create(
                data_object=news_data,
                class_name=collection_name
            )
            return uuid
        except Exception as e:
            logger.error(f"插入新闻失败: {str(e)}")
            return None
    
    def batch_insert_news(
        self,
        collection_name: str,
        news_list: List[Dict[str, Any]],
        batch_size: int = 20
    ) -> int:
        """
        批量插入新闻
        
        Args:
            collection_name: Collection 名称
            news_list: 新闻列表
            batch_size: 批量大小
            
        Returns:
            成功插入的数量
        """
        collection_name = self._format_class_name(collection_name)
        
        if not self.collection_exists(collection_name):
            logger.error(f"Collection 不存在: {collection_name}")
            return 0
        
        success_count = 0
        failed_count = 0
        
        try:
            # 配置批量插入
            self.client.batch.configure(
                batch_size=batch_size,
                dynamic=True,
                timeout_retries=3,
                callback=None
            )
            
            with self.client.batch as batch:
                for idx, news in enumerate(news_list, 1):
                    try:
                        # 检查内容长度（粗略估计）
                        content_length = len(news.get('title', '')) + len(news.get('content', ''))
                        if content_length > 30000:  # 约 8000 tokens
                            logger.warning(f"新闻 #{idx} 内容过长 ({content_length} 字符)，跳过")
                            failed_count += 1
                            continue
                        
                        batch.add_data_object(
                            data_object=news,
                            class_name=collection_name
                        )
                        success_count += 1
                        
                    except Exception as e:
                        failed_count += 1
                        logger.error(f"添加新闻 #{idx} 失败: {str(e)}")
            
            # 检查批量插入结果
            batch_results = self.client.batch.get_batch_stats()
            if batch_results:
                logger.info(f"批量插入统计: {batch_results}")
            
            logger.success(f"批量插入完成: 成功 {success_count}, 失败 {failed_count}, 总计 {len(news_list)}")
            return success_count
        
        except Exception as e:
            logger.error(f"批量插入失败: {str(e)}")
            logger.error(f"已处理: {success_count}, 失败: {failed_count}")
            return success_count
    
    def search_news(
        self,
        collection_name: str,
        query: str,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """
        语义搜索新闻
        
        Args:
            collection_name: Collection 名称
            query: 查询文本
            limit: 返回数量
            
        Returns:
            新闻列表
        """
        collection_name = self._format_class_name(collection_name)
        
        if not self.collection_exists(collection_name):
            logger.error(f"Collection 不存在: {collection_name}")
            return []
        
        try:
            result = (
                self.client.query
                .get(collection_name, [
                    "task_name", "title", "content", "url",
                    "source_name", "published_at", "category", "excerpt"
                ])
                .with_near_text({"concepts": [query]})
                .with_limit(limit)
                .with_additional(["certainty", "id"])
                .do()
            )
            
            items = result['data']['Get'][collection_name]
            return items if items else []
        
        except Exception as e:
            logger.error(f"搜索失败: {str(e)}")
            return []

    def unified_search(
        self,
        collection_name: str,
        query: str,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """
        统一搜索接口：自动处理 NewsArticle 和 NewsChunk 两种 schema

        - 如果是 NewsArticle：直接返回搜索结果
        - 如果是 NewsChunk：按 article_id 分组，拼接同一文章的所有 chunks

        Args:
            collection_name: Collection 名称
            query: 查询文本
            limit: 返回数量（最终文章数）

        Returns:
            统一格式的新闻列表，每篇文章包含完整内容
        """
        collection_name = self._format_class_name(collection_name)

        if not self.collection_exists(collection_name):
            logger.error(f"Collection 不存在: {collection_name}")
            return []

        # 检测 schema 类型
        try:
            schema = self.client.schema.get(collection_name)
            properties = [p['name'] for p in schema['properties']]
            is_chunk_schema = 'article_id' in properties and 'chunk_index' in properties

            if not is_chunk_schema:
                # NewsArticle schema：直接搜索
                logger.debug(f"使用 NewsArticle schema 搜索")
                return self.search_news(collection_name, query, limit)
            else:
                # NewsChunk schema：搜索 + 分组 + 拼接
                logger.debug(f"使用 NewsChunk schema 搜索（需要分组拼接）")
                return self._search_and_merge_chunks(collection_name, query, limit)

        except Exception as e:
            logger.error(f"统一搜索失败: {str(e)}")
            return []

    def _search_and_merge_chunks(
        self,
        collection_name: str,
        query: str,
        limit: int
    ) -> List[Dict[str, Any]]:
        """
        搜索 chunks 并按 article_id 分组拼接

        Args:
            collection_name: Collection 名称
            query: 查询文本
            limit: 最终文章数量

        Returns:
            拼接后的文章列表
        """
        try:
            # 第一步：搜索 chunks（多取一些以保证有足够的文章）
            search_limit = limit * 5  # 假设平均每篇文章 2-3 个 chunks

            result = (
                self.client.query
                .get(collection_name, [
                    "article_id", "chunk_index", "total_chunks",
                    "title", "content", "url", "source_name",
                    "category", "published_at", "excerpt", "task_name"
                ])
                .with_near_text({"concepts": [query]})
                .with_limit(search_limit)
                .with_additional(["certainty", "id"])
                .do()
            )

            chunks = result['data']['Get'].get(collection_name, [])
            if not chunks:
                return []

            logger.debug(f"搜索到 {len(chunks)} 个 chunks")

            # 第二步：提取匹配文章的 article_id
            matched_article_ids = set()
            article_scores = {}  # 记录每篇文章的最高得分

            for chunk in chunks:
                article_id = chunk.get('article_id')
                certainty = chunk.get('_additional', {}).get('certainty', 0)

                if article_id:
                    matched_article_ids.add(article_id)
                    # 保留最高得分
                    if article_id not in article_scores or certainty > article_scores[article_id]:
                        article_scores[article_id] = certainty

            logger.debug(f"匹配到 {len(matched_article_ids)} 篇文章")

            # 第三步：对每篇匹配的文章，查询所有 chunks 并拼接
            merged_articles = []

            for article_id in list(matched_article_ids)[:limit]:  # 限制文章数量
                # 查询该文章的所有 chunks
                article_chunks = self._get_all_chunks_by_article_id(collection_name, article_id)

                if not article_chunks:
                    logger.warning(f"文章 {article_id} 的 chunks 查询失败")
                    continue

                # 按 chunk_index 排序
                article_chunks.sort(key=lambda x: x.get('chunk_index', 0))

                # 拼接完整内容（去掉每个 chunk 的元数据头和索引标记）
                full_content = self._merge_chunk_contents(article_chunks)

                # 使用第一个 chunk 的元数据
                first_chunk = article_chunks[0]

                merged_article = {
                    "id": article_id,
                    "title": first_chunk.get('title', ''),
                    "content": full_content,
                    "url": first_chunk.get('url', ''),
                    "source_name": first_chunk.get('source_name', ''),
                    "category": first_chunk.get('category', ''),
                    "published_at": first_chunk.get('published_at', ''),
                    "excerpt": first_chunk.get('excerpt', ''),
                    "task_name": first_chunk.get('task_name', ''),
                    "_additional": {
                        "certainty": article_scores.get(article_id, 0),
                        "chunk_count": len(article_chunks)
                    }
                }

                merged_articles.append(merged_article)

            # 按相关度排序
            merged_articles.sort(key=lambda x: x['_additional']['certainty'], reverse=True)

            logger.info(f"拼接完成: {len(merged_articles)} 篇文章")

            return merged_articles

        except Exception as e:
            logger.error(f"搜索并合并 chunks 失败: {str(e)}")
            import traceback
            traceback.print_exc()
            return []

    def _get_all_chunks_by_article_id(
        self,
        collection_name: str,
        article_id: str
    ) -> List[Dict[str, Any]]:
        """
        根据 article_id 查询该文章的所有 chunks

        Args:
            collection_name: Collection 名称
            article_id: 文章 ID

        Returns:
            该文章的所有 chunks
        """
        try:
            result = (
                self.client.query
                .get(collection_name, [
                    "article_id", "chunk_index", "total_chunks",
                    "title", "content", "url", "source_name",
                    "category", "published_at", "excerpt", "task_name"
                ])
                .with_where({
                    "path": ["article_id"],
                    "operator": "Equal",
                    "valueString": article_id
                })
                .with_limit(100)  # 假设单篇文章最多 100 个 chunks
                .do()
            )

            chunks = result['data']['Get'].get(collection_name, [])
            return chunks

        except Exception as e:
            logger.error(f"查询文章 {article_id} 的 chunks 失败: {str(e)}")
            return []

    def _merge_chunk_contents(self, chunks: List[Dict[str, Any]]) -> str:
        """
        拼接多个 chunks 的内容，去掉重复的元数据头

        Args:
            chunks: 已排序的 chunk 列表

        Returns:
            拼接后的完整内容
        """
        if not chunks:
            return ""

        # 第一个 chunk 保留完整内容（包含元数据头）
        merged_parts = [chunks[0].get('content', '')]

        # 后续 chunks 去掉元数据头，只保留正文
        for chunk in chunks[1:]:
            content = chunk.get('content', '')

            # 尝试去掉元数据头（寻找【第 X/Y 部分】标记后的内容）
            if '【第' in content and '部分】' in content:
                # 提取【第 X/Y 部分】之后的内容
                parts = content.split('部分】', 1)
                if len(parts) > 1:
                    content = parts[1].strip()

            merged_parts.append(content)

        return '\n\n'.join(merged_parts)

    def delete_item(self, collection_name: str, item_id: str) -> bool:
        """
        删除指定的项目
        
        Args:
            collection_name: Collection 名称
            item_id: 项目的 UUID
            
        Returns:
            是否删除成功
        """
        try:
            self.client.data_object.delete(
                uuid=item_id,
                class_name=collection_name
            )
            logger.info(f"Deleted item {item_id} from {collection_name}")
            return True
        except Exception as e:
            logger.error(f"Delete item error: {e}")
            return False
    
    def hybrid_search(
        self,
        collection_name: str,
        query: str,
        alpha: float = 0.75,
        limit: int = 10,
        similarity_threshold: float = 0.7
    ) -> List[Dict[str, Any]]:
        """
        混合搜索（语义 + 关键词）
        
        Args:
            collection_name: Collection 名称
            query: 查询文本
            alpha: 混合权重 (0=纯关键词, 1=纯语义)
            limit: 返回数量
            similarity_threshold: 相似度阈值
            
        Returns:
            新闻列表
        """
        collection_name = self._format_class_name(collection_name)
        
        if not self.collection_exists(collection_name):
            logger.error(f"Collection 不存在: {collection_name}")
            return []
        
        try:
            result = (
                self.client.query
                .get(collection_name, [
                    "chunk_id", "content", "task_name",
                    "categories", "sources", "article_titles",
                    "article_count", "char_count"
                ])
                .with_hybrid(
                    query=query,
                    alpha=alpha  # 混合权重
                )
                .with_limit(limit)
                .with_additional(["score", "id"])  # 返回分数
                .do()
            )
            
            items = result['data']['Get'][collection_name]
            
            # 过滤低相关结果
            filtered = [
                item for item in items
                if float(item['_additional']['score']) >= similarity_threshold
            ]
            
            logger.info(f"混合搜索完成: 找到 {len(filtered)}/{len(items)} 条相关结果")
            return filtered
        
        except Exception as e:
            logger.error(f"混合搜索失败: {str(e)}")
            return []
    
    def batch_insert_chunks(
        self,
        collection_name: str,
        chunks: List[Dict[str, Any]],
        batch_size: int = 5
    ) -> int:
        """
        批量插入 chunks
        
        Args:
            collection_name: Collection 名称
            chunks: Chunk 列表
            batch_size: 批量大小
            
        Returns:
            成功插入的数量
        """
        collection_name = self._format_class_name(collection_name)
        
        if not self.collection_exists(collection_name):
            logger.error(f"Collection 不存在: {collection_name}")
            return 0
        
        success_count = 0
        failed_count = 0
        
        # 定义错误回调
        errors = []
        def check_batch_result(results):
            if results is not None:
                for result in results:
                    if 'result' in result and 'errors' in result['result']:
                        if 'error' in result['result']['errors']:
                            err_msg = result['result']['errors']['error']
                            errors.append(err_msg)
                            logger.error(f"Weaviate Batch Error: {err_msg}")

        # 配置 Batch
        self.client.batch.configure(
            batch_size=batch_size,
            callback=check_batch_result,
            num_workers=2
        )

        try:
            with self.client.batch as batch:
                for idx, chunk in enumerate(chunks, 1):
                    try:
                        batch.add_data_object(
                            data_object=chunk,
                            class_name=collection_name
                        )
                        success_count += 1
                        
                    except Exception as e:
                        failed_count += 1
                        logger.error(f"添加 chunk #{idx} 失败: {str(e)}")
            
            # 检查是否有回调捕获的错误
            if errors:
                logger.error(f"批量插入存在 {len(errors)} 个错误")
                # 调整成功计数（虽然不太准确，因为 success_count 只是提交数）
                failed_count += len(errors)
                success_count -= len(errors)

            logger.success(f"批量插入完成: 提交 {len(chunks)}, 成功 {success_count}, 失败 {failed_count}")
            return success_count
        
        except Exception as e:
            logger.error(f"批量插入失败: {str(e)}")
            return 0

    def get_existing_urls(self, collection_name: str, task_name: str) -> Set[str]:
        """
        获取已存在的文章 URL 集合
        
        Args:
            collection_name: Collection 名称
            task_name: 任务名称
            
        Returns:
            URL 集合
        """
        collection_name = self._format_class_name(collection_name)
        
        if not self.collection_exists(collection_name):
            return set()
            
        try:
            # 查询所有 chunks 的 article_urls
            # 限制 10000 条，对于目前规模足够
            result = (
                self.client.query
                .get(collection_name, ["article_urls"])
                .with_where({
                    "path": ["task_name"],
                    "operator": "Equal",
                    "valueString": task_name
                })
                .with_limit(10000) 
                .do()
            )
            
            items = result.get('data', {}).get('Get', {}).get(collection_name, [])
            
            existing_urls = set()
            for item in items:
                urls = item.get('article_urls', [])
                if urls:
                    existing_urls.update(urls)
                    
            logger.info(f"从 Weaviate 获取到 {len(existing_urls)} 个已存在 URL")
            return existing_urls
            
        except Exception as e:
            # 如果属性不存在（旧 schema），可能会报错，忽略错误返回空集合
            logger.warning(f"获取已存在 URL 失败 (可能是旧 Schema): {str(e)}")
            return set()
