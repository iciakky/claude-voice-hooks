# Phase 1 测试快速开始指南

## 🚀 5 分钟快速开始

### 1. 安装依赖

```bash
# 进入项目目录
cd F:\repo\claude-voice-hooks

# 安装测试依赖
pip install -r tests/requirements.txt
```

### 2. 运行测试（验证安装）

```bash
# 运行所有测试
pytest tests/ -v

# 预期结果：所有测试当前都是 PASSED（注释状态）或 skipped
```

### 3. 理解测试结构

```
tests/
├── test_config.py          # 配置测试
├── test_queue_handler.py   # 队列测试
├── test_app.py            # API 端点测试
├── test_integration.py    # 集成测试
└── test_performance.py    # 性能测试
```

## 📖 开发工作流（TDD）

### Phase 1 实现流程

#### 步骤 1: 实现配置加载模块

```bash
# 1. 创建文件
mkdir server
touch server/config.py

# 2. 实现 config.py
# ... 编写代码 ...

# 3. 取消注释测试
# 在 tests/test_config.py 中取消注释测试代码

# 4. 运行测试
pytest tests/test_config.py -v

# 5. 修复失败的测试
# 根据测试失败信息修改代码

# 6. 重复步骤 4-5 直到全部通过
```

#### 步骤 2: 实现队列处理

```bash
# 1. 创建文件
touch server/queue_handler.py

# 2. 取消注释 tests/test_queue_handler.py
# 3. 运行测试并修复
pytest tests/test_queue_handler.py -v
```

#### 步骤 3: 实现 FastAPI 应用

```bash
# 1. 创建文件
touch server/app.py

# 2. 取消注释 tests/test_app.py
# 3. 运行测试并修复
pytest tests/test_app.py -v
```

#### 步骤 4: 集成测试

```bash
# 所有模块实现后
pytest tests/test_integration.py -v
```

#### 步骤 5: 性能验证

```bash
# 启动 server
python start_server.py

# 在另一个终端运行性能测试
pytest tests/test_performance.py -v --durations=10
```

## 🎯 测试命令备忘单

### 基本运行

```bash
# 运行所有测试
pytest tests/

# 运行特定文件
pytest tests/test_config.py

# 运行特定类
pytest tests/test_config.py::TestConfigLoader

# 运行特定测试
pytest tests/test_config.py::TestConfigLoader::test_load_default_config
```

### 调试

```bash
# 显示 print 输出
pytest tests/test_config.py -s

# 详细输出
pytest tests/test_config.py -vv

# 失败时进入调试器
pytest tests/test_config.py --pdb

# 第一个失败后停止
pytest tests/ -x
```

### 覆盖率

```bash
# 生成覆盖率报告
pytest tests/ --cov=server --cov-report=html

# 查看报告
start htmlcov/index.html  # Windows
```

### 性能测试

```bash
# 运行性能测试
pytest tests/test_performance.py -v

# 显示最慢的 10 个测试
pytest tests/ --durations=10

# 只运行快速测试
pytest tests/ -m "not slow"
```

## 🔍 示例：编写第一个测试

### 1. 在 `tests/test_config.py` 中找到注释的测试

```python
def test_load_default_config(self, test_config: Dict[str, Any]):
    """Test loading configuration with default values."""
    # This test will work once server/config.py is implemented
    # For now, we test the expected structure
    assert "server" in test_config
    assert "audio_selector" in test_config
    assert "model_provider" in test_config

    assert test_config["server"]["host"] == "127.0.0.1"
    assert test_config["server"]["port"] == 8765
```

### 2. 实现 `server/config.py`

```python
# server/config.py
import yaml
from pathlib import Path
from typing import Dict, Any

def load_config(config_file: str = "config.yaml") -> Dict[str, Any]:
    """Load configuration from YAML file."""
    with open(config_file, 'r') as f:
        config = yaml.safe_load(f)
    return config
```

### 3. 取消注释并运行测试

```python
def test_load_default_config(self, test_config: Dict[str, Any]):
    """Test loading configuration with default values."""
    # 取消注释实际测试代码
    from server.config import load_config

    config = load_config()
    assert "server" in config
    assert config["server"]["host"] == "127.0.0.1"
```

```bash
pytest tests/test_config.py::TestConfigLoader::test_load_default_config -v
```

## 📊 理解测试输出

### 成功的测试

```
tests/test_config.py::TestConfigLoader::test_load_default_config PASSED [100%]
```

### 失败的测试

```
tests/test_config.py::TestConfigLoader::test_load_default_config FAILED [100%]

_________________________________ FAILURES _________________________________
________________ TestConfigLoader.test_load_default_config ________________

    def test_load_default_config(self):
>       assert config["server"]["port"] == 8765
E       AssertionError: assert 9000 == 8765
E        +  where 9000 = {'port': 9000, 'host': '127.0.0.1'}['port']
```

### 跳过的测试

```
tests/test_config.py::TestConfigLoader::test_future_feature SKIPPED [100%]
```

## ⚡ 提示和技巧

### 1. 使用 fixtures

```python
def test_with_fixture(self, test_config, mock_ollama_client):
    # test_config 和 mock_ollama_client 自动注入
    assert test_config is not None
```

### 2. 异步测试

```python
@pytest.mark.asyncio
async def test_async_function():
    result = await some_async_function()
    assert result is not None
```

### 3. 参数化测试

```python
@pytest.mark.parametrize("port", [8765, 8080, 9000])
def test_different_ports(port):
    # 测试会运行 3 次，每次使用不同的 port 值
    config = {"server": {"port": port}}
    assert validate_port(config["server"]["port"])
```

### 4. 临时文件

```python
def test_with_temp_file(tmp_path):
    # tmp_path 是一个临时目录，测试后自动清理
    test_file = tmp_path / "test.yaml"
    test_file.write_text("test: data")
    assert test_file.exists()
```

## 🐛 常见问题

### Q: 测试不运行？

```bash
# 确保在项目根目录
cd F:\repo\claude-voice-hooks

# 确保 pytest 已安装
pip install pytest

# 确认 pytest 能找到测试
pytest --collect-only
```

### Q: Import 错误？

```bash
# 确保 Python 能找到模块
export PYTHONPATH="${PYTHONPATH}:${PWD}"  # Linux/Mac
set PYTHONPATH=%PYTHONPATH%;%CD%           # Windows
```

### Q: 异步测试失败？

```bash
# 确保安装了 pytest-asyncio
pip install pytest-asyncio

# 检查 pytest.ini 配置
# asyncio_mode = auto
```

## 📚 下一步

1. 阅读 [完整测试文档](README.md)
2. 查看 [Phase 1 实现计划](../C:\Users\Chorld220111\.claude\plans\sequential-wondering-ullman.md)
3. 开始实现第一个模块（推荐从 `server/config.py` 开始）
4. 运行测试并迭代

## 🎓 学习资源

- [pytest 文档](https://docs.pytest.org/)
- [pytest-asyncio](https://pytest-asyncio.readthedocs.io/)
- [FastAPI 测试](https://fastapi.tiangolo.com/tutorial/testing/)

---

**准备好了吗？让我们开始 TDD 之旅！** 🚀

```bash
# 第一步：安装依赖
pip install -r tests/requirements.txt

# 第二步：验证测试框架
pytest tests/ -v

# 第三步：开始实现！
# 创建 server/config.py 并开始编码
```
