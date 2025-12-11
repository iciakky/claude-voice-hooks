# Phase 1 Test Suite

完整的测试套件用于 Claude Voice Hooks Phase 1（Server 核心框架）开发。

## 📋 测试概览

这套测试采用 **TDD（测试驱动开发）** 方式编写，定义了 Phase 1 各组件的预期行为。测试分为以下几类：

### 测试类型

1. **单元测试** - 测试单个组件功能
   - `test_config.py` - 配置加载和验证
   - `test_queue_handler.py` - 请求队列处理

2. **集成测试** - 测试组件间交互
   - `test_app.py` - FastAPI 应用端点
   - `test_integration.py` - 端到端流程

3. **性能测试** - 验证性能要求
   - `test_performance.py` - 响应时间、吞吐量、并发

## 🎯 测试目标

Phase 1 的核心测试目标：

- ✅ **HTTP 响应时间** < 100ms
- ✅ **模型预热时间** < 5s
- ✅ **队列操作** < 50ms
- ✅ **端到端流程** < 30s（包含模型推理）
- ✅ **并发请求处理** - 支持 10+ 并发

## 🚀 快速开始

### 安装测试依赖

```bash
pip install -r tests/requirements.txt
```

### 运行所有测试

```bash
# 运行所有测试
pytest tests/ -v

# 运行特定测试文件
pytest tests/test_config.py -v

# 运行特定测试类
pytest tests/test_app.py::TestHealthEndpoint -v

# 运行特定测试
pytest tests/test_app.py::TestHealthEndpoint::test_health_endpoint_returns_ok -v
```

### 运行性能测试

```bash
# 运行性能测试并显示最慢的 10 个测试
pytest tests/test_performance.py -v --durations=10

# 只运行响应时间测试
pytest tests/test_performance.py::TestResponseTime -v
```

### 生成测试覆盖率报告

```bash
# 生成覆盖率报告
pytest tests/ --cov=server --cov-report=html

# 在浏览器中查看报告
start htmlcov/index.html  # Windows
open htmlcov/index.html   # macOS
```

## 📁 测试文件结构

```
tests/
├── conftest.py                    # pytest 配置和共享 fixtures
├── README.md                      # 本文档
├── requirements.txt               # 测试依赖
│
├── test_config.py                 # 配置加载测试
├── test_queue_handler.py          # 队列处理测试
├── test_app.py                    # FastAPI 端点测试
├── test_integration.py            # 端到端集成测试
├── test_performance.py            # 性能测试
│
├── fixtures/                      # 测试数据
│   ├── sample_transcript.md       # 示例对话记录
│   └── test_config.yaml           # 测试配置
│
└── mocks/                         # Mock 对象
    └── mock_ollama.py             # Mock Ollama 响应
```

## 🧪 测试用例说明

### 1. 配置加载测试 (`test_config.py`)

测试配置加载和验证逻辑：

- ✅ 从 YAML 文件加载配置
- ✅ 环境变量覆盖配置
- ✅ 配置验证（端口范围、目录存在性等）
- ✅ 默认值处理
- ✅ 配置与组件集成

**关键测试：**

```python
# 测试环境变量覆盖
def test_env_var_override(env_vars):
    assert os.getenv("SERVER_PORT") == "8765"
    # config = load_config()
    # assert config["server"]["port"] == 8765

# 测试无效配置
def test_invalid_port_number():
    # 端口应在 1024-65535 范围内
    # with pytest.raises(ValueError):
    #     validate_config({"server": {"port": 0}})
```

### 2. 队列处理测试 (`test_queue_handler.py`)

测试异步请求队列处理：

- ✅ 添加/获取请求
- ✅ FIFO 顺序
- ✅ 并发处理
- ✅ 错误恢复
- ✅ 指标收集

**关键测试：**

```python
# 测试 FIFO 顺序
@pytest.mark.asyncio
async def test_queue_fifo_order():
    # 验证请求按顺序处理

# 测试错误后继续处理
@pytest.mark.asyncio
async def test_processor_continues_on_error():
    # 一个请求失败不应影响后续请求
```

### 3. FastAPI 端点测试 (`test_app.py`)

测试 HTTP 端点功能：

- ✅ `POST /hook` - 接收 hook 请求
- ✅ `GET /health` - 健康检查
- ✅ 请求验证
- ✅ 错误响应
- ✅ 启动/关闭

**关键测试：**

```python
# 测试 hook 端点
@pytest.mark.asyncio
async def test_hook_endpoint_accepts_valid_request():
    # response = await client.post("/hook", json=request)
    # assert response.status_code == 202
    # assert response.json()["status"] == "accepted"

# 测试响应时间
@pytest.mark.asyncio
async def test_hook_endpoint_response_time():
    # 应在 < 100ms 内响应
```

### 4. 集成测试 (`test_integration.py`)

测试完整流程：

- ✅ Hook → Server → 队列 → 处理 → 音频
- ✅ 多个 hook 顺序触发
- ✅ 并发 hook 触发
- ✅ Fallback 机制
- ✅ 错误恢复

**关键测试：**

```python
# 测试完整流程
@pytest.mark.asyncio
async def test_successful_hook_flow_end_to_end():
    # 1. 发送请求
    # 2. 验证立即返回（< 100ms）
    # 3. 等待后台处理
    # 4. 验证处理成功

# 测试 fallback
@pytest.mark.asyncio
async def test_fallback_when_server_unavailable():
    # Server 不可用时应 fallback 到本地处理
```

### 5. 性能测试 (`test_performance.py`)

验证性能要求：

- ✅ HTTP 响应 < 100ms
- ✅ 模型预热 < 5s
- ✅ 队列操作 < 50ms
- ✅ 端到端 < 30s
- ✅ 并发处理能力

**关键测试：**

```python
# 测试响应时间
@pytest.mark.asyncio
async def test_hook_endpoint_response_under_100ms():
    # 测量并验证响应时间

# 测试并发
@pytest.mark.asyncio
async def test_concurrent_50_requests():
    # 测试 50 个并发请求的处理
```

## 🔧 使用 Fixtures

测试使用了多个共享 fixtures（定义在 `conftest.py`）：

### 常用 Fixtures

```python
# 测试配置
def test_example(test_config):
    assert test_config["server"]["port"] == 8765

# 示例请求
def test_example(sample_hook_request):
    assert sample_hook_request["event"] == "PostToolUse"

# Mock Ollama
def test_example(mock_ollama_client):
    response = await mock_ollama_client.generate(...)

# 临时文件
def test_example(tmp_path):
    test_file = tmp_path / "test.txt"
    test_file.write_text("test")

# 音频文件结构
def test_example(audio_files_structure):
    audio_root = audio_files_structure["root"]
    completion_files = audio_files_structure["files"]["completion"]
```

## 📊 测试报告

### 生成详细报告

```bash
# HTML 报告
pytest tests/ --html=report.html --self-contained-html

# JUnit XML（CI/CD）
pytest tests/ --junitxml=junit.xml

# 覆盖率 + HTML
pytest tests/ --cov=server --cov-report=html --cov-report=term
```

### 查看测试统计

```bash
# 显示最慢的测试
pytest tests/ --durations=0

# 只显示摘要
pytest tests/ -q

# 显示详细输出
pytest tests/ -vv
```

## 🎨 编写新测试

### 单元测试模板

```python
"""Test for new_module.py"""
import pytest

class TestNewFeature:
    """Test new feature functionality."""

    def test_basic_functionality(self):
        """Test basic feature behavior."""
        # Arrange
        input_data = {"key": "value"}

        # Act
        # result = new_function(input_data)

        # Assert
        # assert result == expected_output
        pass

    @pytest.mark.asyncio
    async def test_async_functionality(self):
        """Test async feature behavior."""
        # result = await async_function()
        # assert result is not None
        pass
```

### 集成测试模板

```python
"""Integration test for feature X"""
import pytest

class TestFeatureXIntegration:
    """Test feature X integration with other components."""

    @pytest.mark.asyncio
    async def test_complete_flow(self, test_config, mock_dependencies):
        """Test complete flow from input to output."""
        # Setup
        # component = create_component(test_config)

        # Execute
        # result = await component.process()

        # Verify
        # assert result.success is True
        pass
```

## 🐛 调试测试

### 运行特定测试并查看输出

```bash
# 显示 print 输出
pytest tests/test_config.py -v -s

# 进入调试器
pytest tests/test_config.py --pdb

# 在失败时进入调试器
pytest tests/ --pdb --maxfail=1
```

### 使用标记

```python
# 标记慢速测试
@pytest.mark.slow
def test_slow_operation():
    pass

# 跳过测试
@pytest.mark.skip(reason="Not implemented yet")
def test_future_feature():
    pass

# 预期失败
@pytest.mark.xfail
def test_known_bug():
    pass
```

运行标记的测试：

```bash
# 只运行慢速测试
pytest tests/ -v -m slow

# 排除慢速测试
pytest tests/ -v -m "not slow"
```

## 🔄 持续集成

### GitHub Actions 示例

```yaml
name: Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest

    steps:
      - uses: actions/checkout@v2

      - name: Set up Python
        uses: actions/setup-python@v2
        with:
          python-version: '3.11'

      - name: Install dependencies
        run: |
          pip install -r requirements.txt
          pip install -r tests/requirements.txt

      - name: Run tests
        run: pytest tests/ -v --cov=server --cov-report=xml

      - name: Upload coverage
        uses: codecov/codecov-action@v2
```

## 📝 注意事项

### TDD 工作流

这些测试是在实际代码之前编写的（TDD 方式），因此：

1. **测试定义预期行为** - 测试描述了代码应该如何工作
2. **实现时运行测试** - 实现代码时运行测试验证
3. **测试驱动设计** - 测试帮助设计更好的 API

### 当前状态

- ✅ 测试框架已完成
- ✅ 测试用例已定义
- ⏳ 等待 Phase 1 代码实现
- ⏳ 实现后取消注释测试代码

### 实现 Phase 1 时的工作流

1. 实现一个模块（如 `server/config.py`）
2. 取消注释对应测试（`test_config.py`）
3. 运行测试：`pytest tests/test_config.py -v`
4. 修复失败的测试
5. 重复直到所有测试通过

## 🔗 相关文档

- [Phase 1 实现计划](../C:\Users\Chorld220111\.claude\plans\sequential-wondering-ullman.md)
- [项目 README](../README.md)
- [pytest 文档](https://docs.pytest.org/)

## 🤝 贡献

添加新测试时：

1. 遵循现有的测试结构和命名约定
2. 为每个测试添加清晰的 docstring
3. 使用合适的 fixtures
4. 确保测试是独立的（不依赖其他测试）
5. 更新本文档

## 📞 获取帮助

如果测试不通过或有问题：

1. 检查测试日志：`pytest tests/ -v`
2. 查看覆盖率报告找到未测试的代码
3. 使用调试器：`pytest tests/ --pdb`
4. 查阅 pytest 文档

---

**测试是代码质量的保证。让我们用测试驱动 Phase 1 的开发！** 🚀
