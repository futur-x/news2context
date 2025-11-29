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
    
    # NewsChunk Schema 定义（智能切割）
    NEWS_CHUNK_SCHEMA = {
        "class": "NewsChunk",
        "description": "新闻 Chunk（智能切割，多篇新闻合并）",
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
                "name": "chunk_id",
                "dataType": ["string"],
                "description": "Chunk 唯一标识",
                "moduleConfig": {
                    "text2vec-openai": {
                        "skip": True
                    }
                }
            },
            {
                "name": "content",
                "dataType": ["text"],
                "description": "Chunk 内容（多篇新闻合并）"
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
                "name": "categories",
                "dataType": ["string[]"],
                "description": "包含的分类"
            },
            {
                "name": "sources",
                "dataType": ["string[]"],
                "description": "包含的新闻源"
            },
            {
                "name": "article_titles",
                "dataType": ["string[]"],
                "description": "包含的新闻标题"
            },
            {
                "name": "article_count",
                "dataType": ["int"],
                "description": "包含的新闻数量",
                "moduleConfig": {
                    "text2vec-openai": {
                        "skip": True
                    }
                }
            },
            {
                "name": "char_count",
                "dataType": ["int"],
                "description": "字符数",
                "moduleConfig": {
                    "text2vec-openai": {
                        "skip": True
                    }
                }
            },
            {
                "name": "article_urls",
                "dataType": ["string[]"],
                "description": "包含的文章链接",
                "moduleConfig": {
                    "text2vec-openai": {
                        "skip": True
                    }
                }
            },
            {
                "name": "created_at",
                "dataType": ["date"],
                "description": "创建时间"
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
