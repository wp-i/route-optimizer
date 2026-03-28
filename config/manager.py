"""配置管理"""

import json
import os
from pathlib import Path
from datetime import datetime
from typing import Optional


class ConfigManager:
    """API Key 配置管理"""
    
    CONFIG_DIR = Path.home() / ".qclaw"
    CONFIG_FILE = CONFIG_DIR / "route-optimizer-config.json"
    
    @classmethod
    def get_api_key(cls) -> Optional[str]:
        """
        获取 API Key
        
        Returns:
            API Key 或 None（未配置时）
        """
        if not cls.CONFIG_FILE.exists():
            return None
        
        try:
            with open(cls.CONFIG_FILE, 'r', encoding='utf-8') as f:
                config = json.load(f)
                return config.get('amap_api_key')
        except (json.JSONDecodeError, IOError):
            return None
    
    @classmethod
    def set_api_key(cls, api_key: str) -> None:
        """
        保存 API Key
        
        Args:
            api_key: 高德地图 API Key
        """
        cls.CONFIG_DIR.mkdir(parents=True, exist_ok=True)
        
        now = datetime.now().isoformat()
        
        # 读取现有配置（如果有）
        config = {
            "amap_api_key": api_key,
            "created_at": now,
            "updated_at": now
        }
        
        if cls.CONFIG_FILE.exists():
            try:
                with open(cls.CONFIG_FILE, 'r', encoding='utf-8') as f:
                    old = json.load(f)
                    config['created_at'] = old.get('created_at', now)
            except (json.JSONDecodeError, IOError):
                pass
        
        # 写入配置
        with open(cls.CONFIG_FILE, 'w', encoding='utf-8') as f:
            json.dump(config, f, indent=2, ensure_ascii=False)
        
        # 设置文件权限（仅 Unix 系统）
        if os.name != 'nt':
            try:
                os.chmod(cls.CONFIG_FILE, 0o600)
            except OSError:
                pass
    
    @classmethod
    def mask_api_key(cls, api_key: str) -> str:
        """
        脱敏显示 API Key
        
        Args:
            api_key: 原始 API Key
        
        Returns:
            脱敏后的 API Key（如 "abcd****efgh"）
        """
        if not api_key:
            return ""
        
        if len(api_key) <= 8:
            return '*' * len(api_key)
        
        return api_key[:4] + '*' * (len(api_key) - 8) + api_key[-4:]
    
    @classmethod
    def is_configured(cls) -> bool:
        """检查是否已配置 API Key"""
        return cls.get_api_key() is not None
    
    @classmethod
    def clear_config(cls) -> None:
        """清除配置"""
        if cls.CONFIG_FILE.exists():
            cls.CONFIG_FILE.unlink()
