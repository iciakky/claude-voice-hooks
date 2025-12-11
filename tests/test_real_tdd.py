"""
真实的 TDD 测试示例 - 这些测试会失败直到代码被实现

这个文件演示了正确的 TDD 流程：
1. 写一个会失败的测试（红色）
2. 实现最小代码使其通过（绿色）
3. 重构（保持绿色）

运行这个文件应该看到失败（这是期望的！）：
    pytest tests/test_real_tdd.py -v

这些测试会在你实现 Phase 1 代码时逐渐变绿。
"""
import pytest
from pathlib import Path
import sys

# 添加项目根目录到 path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


class TestServerDirectory:
    """测试 server 目录和基础结构。"""

    def test_server_directory_exists(self):
        """测试 server 目录是否存在（第一步：创建目录）。"""
        server_dir = project_root / "server"

        # 这个测试会失败直到你创建 server 目录
        assert server_dir.exists(), (
            "server/ 目录不存在。\n"
            "修复方法：mkdir server"
        )

    def test_server_is_python_package(self):
        """测试 server 是否是 Python 包。"""
        server_init = project_root / "server" / "__init__.py"

        # 这个测试会失败直到你创建 __init__.py
        assert server_init.exists(), (
            "server/__init__.py 不存在。\n"
            "修复方法：touch server/__init__.py"
        )


class TestConfigModule:
    """测试 config 模块（TDD 的开始）。"""

    def test_config_module_exists(self):
        """测试 config.py 文件是否存在。"""
        config_file = project_root / "server" / "config.py"

        assert config_file.exists(), (
            "server/config.py 不存在。\n"
            "修复方法：创建这个文件并开始实现"
        )

    def test_config_module_can_import(self):
        """测试能否导入 config 模块。"""
        try:
            from server import config
            assert True, "config 模块成功导入"
        except ImportError as e:
            pytest.fail(
                f"无法导入 server.config 模块。\n"
                f"错误: {e}\n"
                f"修复方法：实现 server/config.py"
            )

    def test_load_config_function_exists(self):
        """测试 load_config 函数是否存在。"""
        try:
            from server.config import load_config
            assert callable(load_config), "load_config 应该是可调用的函数"
        except ImportError as e:
            pytest.fail(
                f"无法导入 load_config 函数。\n"
                f"错误: {e}\n"
                f"修复方法：在 server/config.py 中实现 load_config() 函数"
            )

    @pytest.mark.skip(reason="取消注释这行并实现 load_config 后运行")
    def test_load_config_returns_dict(self):
        """测试 load_config 返回字典。"""
        # 取消注释下面的代码来启用这个测试
        # from server.config import load_config
        # config = load_config()
        # assert isinstance(config, dict), "load_config 应该返回字典"
        # assert "server" in config, "配置应该包含 'server' 键"
        pass


class TestAppModule:
    """测试 FastAPI app 模块。"""

    def test_app_module_exists(self):
        """测试 app.py 文件是否存在。"""
        app_file = project_root / "server" / "app.py"
        assert app_file.exists(), "server/app.py 不存在"

    def test_app_can_import(self):
        """测试能否导入 FastAPI app。"""
        from server.app import app
        assert app is not None, "app 应该不为 None"
        assert app.title == "Claude Voice Hooks Server", "app 标题应该正确设置"


class TestTDDExample:
    """TDD 示例：从测试开始设计 API。"""

    @pytest.mark.skip(reason="演示用例")
    def test_example_tdd_workflow(self):
        """
        这是一个 TDD 工作流示例：

        步骤 1（红色）：写一个会失败的测试
        """
        # 假设我们要实现一个 greet() 函数
        # from server.utils import greet

        # 步骤 2：定义预期行为
        # result = greet("World")
        # assert result == "Hello, World!"

        """
        步骤 3（运行测试）：
            pytest tests/test_real_tdd.py::TestTDDExample -v
            ❌ 失败：ModuleNotFoundError: No module named 'server.utils'

        步骤 4（绿色）：实现最小代码
            # server/utils.py
            def greet(name):
                return f"Hello, {name}!"

        步骤 5（再次运行）：
            pytest tests/test_real_tdd.py::TestTDDExample -v
            ✅ 通过！

        步骤 6（重构）：优化代码，保持测试通过
        """
        pass


if __name__ == "__main__":
    print("=" * 60)
    print("真实 TDD 测试 - 期望看到失败（这是正常的！）")
    print("=" * 60)
    print("\n运行命令：pytest tests/test_real_tdd.py -v\n")
    print("这些测试会在你实现代码时逐渐变绿。")
    print("=" * 60)

    pytest.main([__file__, "-v", "--tb=short"])
