"""
配置管理模块
负责加载和验证系统配置
"""

import os
from pathlib import Path
from typing import Dict, Any, Optional
import yaml
from dotenv import load_dotenv
from loguru import logger


class ConfigManager:
    """配置管理器"""
    
    def __init__(self, config_path: Optional[str] = None):
        """
        初始化配置管理器
        
        Args:
            config_path: 配置文件路径，默认为 config/config.yaml
        """
        # 确定项目根目录
        project_root = Path(__file__).parent.parent.parent
        
        # 加载环境变量 (优先加载 config/.env)
        env_path = project_root / "config" / ".env"
        load_dotenv(dotenv_path=env_path)
        
        # 确定配置文件路径
        if config_path is None:
            config_path = project_root / "config" / "config.yaml"
        
        self.config_path = Path(config_path)
        self._config: Dict[str, Any] = {}
        self._load_config()
    
    def _load_config(self):
        """加载配置文件"""
        if not self.config_path.exists():
            raise FileNotFoundError(f"配置文件不存在: {self.config_path}")
        
        with open(self.config_path, 'r', encoding='utf-8') as f:
            self._config = yaml.safe_load(f)
        
        # 从环境变量覆盖敏感配置
        self._override_from_env()
        
        logger.info(f"配置已加载: {self.config_path}")
    
    def _override_from_env(self):
        """从环境变量覆盖配置"""
        # LLM 配置
        if api_key := os.getenv('OPENAI_API_KEY'):
            self._config['llm']['api_key'] = api_key
        if base_url := os.getenv('OPENAI_BASE_URL'):
            self._config['llm']['base_url'] = base_url
        
        # TopHub 配置
        if tophub_key := os.getenv('TOPHUB_API_KEY'):
            self._config['news_sources']['engines']['tophub']['api_key'] = tophub_key
        
        # Weaviate 配置
        if weaviate_url := os.getenv('WEAVIATE_URL'):
            self._config['weaviate']['url'] = weaviate_url
        if weaviate_key := os.getenv('WEAVIATE_API_KEY'):
            self._config['weaviate']['api_key'] = weaviate_key
        
        # API 配置
        if api_host := os.getenv('API_HOST'):
            self._config['api']['host'] = api_host
        if api_port := os.getenv('API_PORT'):
            self._config['api']['port'] = int(api_port)
    
    def get(self, key: str, default: Any = None) -> Any:
        """
        获取配置项
        
        Args:
            key: 配置键，支持点号分隔，如 'llm.api_key'
            default: 默认值
            
        Returns:
            配置值
        """
        keys = key.split('.')
        value = self._config
        
        for k in keys:
            if isinstance(value, dict):
                value = value.get(k)
            else:
                return default
            
            if value is None:
                return default
        
        return value
    
    def set(self, key: str, value: Any):
        """
        设置配置项
        
        Args:
            key: 配置键，支持点号分隔
            value: 配置值
        """
        keys = key.split('.')
        config = self._config
        
        for k in keys[:-1]:
            if k not in config:
                config[k] = {}
            config = config[k]
        
        config[keys[-1]] = value
    
    def save(self):
        """保存配置到文件"""
        with open(self.config_path, 'w', encoding='utf-8') as f:
            yaml.dump(self._config, f, allow_unicode=True, default_flow_style=False)
        
        logger.info(f"配置已保存: {self.config_path}")
    
    def validate(self) -> bool:
        """
        验证配置完整性
        
        Returns:
            是否有效
        """
        errors = []
        
        # 验证 LLM 配置
        if not self.get('llm.api_key'):
            errors.append("LLM API Key 未配置")
        
        # 验证新闻源引擎配置
        active_engine = self.get('news_sources.active_engine')
        if not active_engine:
            errors.append("未指定活跃的新闻源引擎")
        else:
            engine_config = self.get(f'news_sources.engines.{active_engine}')
            if not engine_config:
                errors.append(f"引擎 {active_engine} 配置不存在")
            elif not engine_config.get('enabled'):
                errors.append(f"引擎 {active_engine} 未启用")
            elif active_engine == 'tophub' and not engine_config.get('api_key'):
                errors.append("TopHub API Key 未配置")
        
        # 验证 Weaviate 配置
        if not self.get('weaviate.url'):
            errors.append("Weaviate URL 未配置")
        
        if errors:
            for error in errors:
                logger.error(f"配置验证失败: {error}")
            return False
        
        logger.success("配置验证通过")
        return True
    
    @property
    def config(self) -> Dict[str, Any]:
        """获取完整配置"""
        return self._config


# 全局配置实例
_config_instance: Optional[ConfigManager] = None


def get_config() -> ConfigManager:
    """获取全局配置实例"""
    global _config_instance
    if _config_instance is None:
        _config_instance = ConfigManager()
    return _config_instance


def reload_config():
    """重新加载配置"""
    global _config_instance
    _config_instance = None
    return get_config()
