"""
Smoke tests - 立即可运行的基础测试

这些测试验证测试框架本身是否正常工作，
以及基本的环境配置是否正确。

这些测试应该立即通过（绿色），证明测试框架正常。
"""
import pytest
import sys
from pathlib import Path


class TestTestFramework:
    """验证测试框架本身是否正常工作。"""

    def test_pytest_is_working(self):
        """验证 pytest 正常工作。"""
        assert True, "pytest should be able to run this test"

    def test_python_version(self):
        """验证 Python 版本。"""
        assert sys.version_info >= (3, 8), "Python 3.8+ required"

    def test_project_structure(self):
        """验证项目目录结构。"""
        project_root = Path(__file__).parent.parent
        assert project_root.exists()
        assert (project_root / "audio").exists(), "audio directory should exist"
        assert (project_root / "README.md").exists(), "README should exist"


class TestFixtures:
    """验证 fixtures 是否正常工作。"""

    def test_test_data_dir_fixture(self, test_data_dir):
        """验证 test_data_dir fixture。"""
        assert test_data_dir.exists()
        assert test_data_dir.is_dir()

    def test_sample_transcript_fixture(self, sample_transcript):
        """验证 sample_transcript fixture。"""
        assert sample_transcript is not None
        assert len(sample_transcript) > 0
        assert "Conversation" in sample_transcript or "Assistant" in sample_transcript

    def test_sample_hook_request_fixture(self, sample_hook_request):
        """验证 sample_hook_request fixture。"""
        assert "event" in sample_hook_request
        assert "tool_name" in sample_hook_request
        assert sample_hook_request["event"] == "PostToolUse"

    def test_test_config_fixture(self, test_config):
        """验证 test_config fixture。"""
        assert "server" in test_config
        assert "audio_selector" in test_config
        assert "model_provider" in test_config

    def test_audio_files_structure_fixture(self, audio_files_structure):
        """验证 audio_files_structure fixture。"""
        assert "root" in audio_files_structure
        assert "files" in audio_files_structure
        assert "completion" in audio_files_structure["files"]
        assert len(audio_files_structure["files"]["completion"]) > 0


class TestMocks:
    """验证 mock 对象是否正常工作。"""

    def test_mock_ollama_client(self, mock_ollama_client):
        """验证 mock_ollama_client fixture。"""
        assert mock_ollama_client is not None
        assert hasattr(mock_ollama_client, 'generate')

    @pytest.mark.asyncio
    async def test_mock_audio_player(self, mock_audio_player):
        """验证 mock_audio_player fixture。"""
        result = await mock_audio_player("test.wav")
        assert result is True


class TestEnvironment:
    """验证环境配置。"""

    def test_env_vars_fixture(self, env_vars):
        """验证环境变量 fixture。"""
        assert "SERVER_HOST" in env_vars
        assert "SERVER_PORT" in env_vars
        assert env_vars["SERVER_PORT"] == "8765"

    def test_performance_threshold_fixture(self, performance_threshold):
        """验证性能阈值 fixture。"""
        assert "http_response_time_ms" in performance_threshold
        assert "model_warmup_time_s" in performance_threshold
        assert performance_threshold["http_response_time_ms"] == 100


class TestTempFiles:
    """验证临时文件处理。"""

    def test_tmp_path_fixture(self, tmp_path):
        """验证 tmp_path fixture（pytest 内置）。"""
        assert tmp_path.exists()
        assert tmp_path.is_dir()

        # 创建临时文件
        test_file = tmp_path / "test.txt"
        test_file.write_text("test content")
        assert test_file.exists()
        assert test_file.read_text() == "test content"

    def test_mock_transcript_file_fixture(self, mock_transcript_file):
        """验证 mock_transcript_file fixture。"""
        assert mock_transcript_file.exists()
        assert mock_transcript_file.suffix == ".md"
        content = mock_transcript_file.read_text()
        assert len(content) > 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
