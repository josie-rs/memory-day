# memory_day 独立仓库发布前 Checklist

这份清单用于在首次公开 `memory-day` 独立仓库前，确认代码、配置、数据与文档都已准备妥当。

## 一、隐私与敏感信息检查

- [ ] 仓库中不包含真实 `config.py`
- [ ] 仓库中不包含任何真实 API key / app secret / webhook
- [ ] 仓库中不包含 `content/memory_library.json`
- [ ] 仓库中不包含本地日志文件
- [ ] 仓库中不包含导出的临时照片文件
- [ ] 示例数据中不包含真实个人信息

## 二、仓库文件边界检查

建议保留：

- [ ] `memory_day/`
- [ ] `README.md`
- [ ] `config.example.py`
- [ ] `.gitignore`
- [ ] `requirements.txt`
- [ ] `content/memory_library.example.json`

建议不要提交：

- [ ] `config.py`
- [ ] `content/memory_library.json`
- [ ] `__pycache__/`
- [ ] `.DS_Store`

## 三、README 检查

- [ ] 已写明 **macOS-only**
- [ ] 已写明依赖 Photos.app / Photos.sqlite / AppleScript / `sips`
- [ ] 已写明不包含推送、调度和私有数据
- [ ] 已写明配置方式与 CLI 用法

## 四、功能冒烟测试

```bash
python3 -m py_compile memory_day/__init__.py memory_day/service.py memory_day/photos.py memory_day/library.py memory_day/cli.py
python3 -m memory_day.cli prepare-date --date 2026-04-07 --top-n 4
```

- [ ] 编译通过
- [ ] CLI 可运行

## 五、最低发布标准

- [ ] 没有真实密钥
- [ ] 没有真实个人数据
- [ ] README 足够清楚
- [ ] CLI 基本可用
- [ ] `.gitignore` 已生效
