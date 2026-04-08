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
- [ ] 已写明不内置推送通道，用户可自行接入飞书、企业微信、钉钉、Telegram、邮件或自定义 webhook
- [ ] 已写明配置方式与 CLI 用法

## 四、功能冒烟测试

```bash
python3 -m py_compile memory_day/__init__.py memory_day/service.py memory_day/photos.py memory_day/library.py memory_day/cli.py
python3 -m memory_day.cli prepare-date --date 2026-04-07 --top-n 4
```

- [ ] 编译通过
- [ ] CLI 可运行

## 五、验证记录（2026-04-08）

本次做过一轮**不连接真实 Photos.sqlite / 不使用真实照片库**的最小可运行验证，验证方式为：

- 临时创建本地 `config.py`
- 临时创建本地 `content/memory_library.json`
- 将 `PHOTOS_DB_PATH` 指向不存在的测试路径
- 仅验证 CLI 启动、内容库读写和失败路径是否可控

已验证通过：

- `python3 -m py_compile memory_day/__init__.py memory_day/service.py memory_day/photos.py memory_day/library.py memory_day/cli.py`
- `python3 -m memory_day.cli add-entry --date 2026-04-07 --entry-json ...`
- `python3 -m memory_day.cli cleanup-image --image-path ...`
- `python3 -m memory_day.cli get-capture-time --photo-id TEST-PHOTO-001`
- `python3 -m memory_day.cli get-daily-payload --date 2026-04-07`

验证结论：

- CLI 可正常启动
- 本地配置读取正常
- 内容库读写正常
- 在无真实照片库 / 无有效照片 ID 时，失败路径可控，不会直接崩溃

本次未验证：

- 真实 Photos.app / Photos.sqlite 联调
- 真实照片发现与导出
- 真实拍摄时间 / 地点读取
- 基于真实照片的完整 payload 生成

验证结束后，临时创建的 `config.py` 与 `content/memory_library.json` 已清理完成。

## 六、最低发布标准

- [ ] 没有真实密钥
- [ ] 没有真实个人数据
- [ ] README 足够清楚
- [ ] CLI 基本可用
- [ ] `.gitignore` 已生效
