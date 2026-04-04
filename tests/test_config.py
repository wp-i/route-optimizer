"""测试配置管理"""
import pytest
import sys
import json
import tempfile
import os
from pathlib import Path
sys.path.insert(0, '..')

from config.manager import ConfigManager


class TestConfigManager:
    """API Key 配置管理测试"""

    def setup_method(self):
        self._orig_file = ConfigManager.CONFIG_FILE
        self._tmp = tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False, encoding='utf-8')
        self._tmp.close()
        ConfigManager.CONFIG_FILE = Path(self._tmp.name)

    def teardown_method(self):
        ConfigManager.CONFIG_FILE = self._orig_file
        try:
            os.unlink(self._tmp.name)
        except FileNotFoundError:
            pass

    def test_set_and_get_api_key(self):
        ConfigManager.set_api_key('abc123def456')
        assert ConfigManager.get_api_key() == 'abc123def456'

    def test_mask_api_key(self):
        masked = ConfigManager.mask_api_key('690019cfbfcdd40d3cb')
        assert masked.startswith('6900')
        assert masked.endswith('d3cb')
        assert '*' in masked

    def test_mask_short_key(self):
        masked = ConfigManager.mask_api_key('ab')
        assert masked == '**'

    def test_get_when_not_configured(self):
        try:
            os.unlink(self._tmp.name)
        except FileNotFoundError:
            pass
        assert ConfigManager.get_api_key() is None

    def test_clear_config(self):
        ConfigManager.set_api_key('test123')
        ConfigManager.clear_config()
        assert ConfigManager.get_api_key() is None

    def test_is_configured(self):
        assert not ConfigManager.is_configured()
        ConfigManager.set_api_key('test456')
        assert ConfigManager.is_configured()
