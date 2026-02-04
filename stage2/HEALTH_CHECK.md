# 自检机制说明

## 概述

项目已集成自动化健康检查机制，用于在开发和部署前验证系统状态。

## 使用方式

### 运行健康检查

```bash
python health_check.py
```

### 检查项目

健康检查包含以下 6 个方面：

1. **类型检查**
   - 检查关键模块的类型错误
   - 监控文件: monitor.py, monitor_v2.py, web_app.py, core/, sources/
   - 使用 pyright (如果安装) 或备用检查

2. **代码质量**
   - 语法错误检查
   - 关键文件存在性检查
   - 未使用变量/导入检查

3. **配置文件**
   - config.yaml 存在性和格式
   - 关键字段检查 (database.db_path, monitor.interval, ocr.lang)
   - 截图目录可写性

4. **数据库**
   - 数据库连接性
   - 表结构检查 (messages, keywords)
   - 字段完整性检查

5. **Web 应用**
   - Flask 应用可导入
   - 关键路由注册 (/, /messages, /keywords, /api/stats)
   - 模板文件存在性

6. **消息源**
   - 核心模块可导入 (core/message)
   - 消息源模块可导入 (wechat_screen, base)
   - 数据库管理器可导入

## 检查结果解读

### 状态说明

- **[OK]**: 检查通过，无问题
- **[WARN]**: 有警告，但可以运行
- **[ERR]**: 有错误，建议修复后再运行

### 退出码

- **0**: 所有检查通过或有警告
- **1**: 有错误，需要修复

## 已知问题清单

> **权威维护位置**: [DOCS/DEV_NOTES.md](DOCS/DEV_NOTES.md#已知类型警告记录-p1)
> 
> 以下清单为摘要，详细说明和决策记录请查看 DEV_NOTES.md

以下类型错误是已知的，不会影响运行时：

| 文件 | 行号 | 问题 | 影响 | 说明 |
|------|------|------|------|------|
| sources/wechat_screen.py | 112 | window_element 可能为 None | 无 | 运行时已检查 |
| sources/wechat_screen.py | 118 | window_element 可能为 None | 无 | 运行时已检查 |
| sources/window_screen.py | 46 | class_name_patterns 类型 | 无 | 运行时正常 |
| monitor.py | 1396 | heartbeat 属性 | 无 | 运行时正常 |

这些警告是 Pylance 的静态分析限制，实际运行时都有相应的空值检查。

**处理决策**: 暂缓修复，改为在 AI-GENERATED 标记中添加 `[NOTE]` 说明，并在 DEV_NOTES.md 中记录详细原因。

## 开发流程建议

### 每次开发完成后

1. **运行健康检查**
   ```bash
   python health_check.py
   ```

2. **检查报告**
   - 如果有 [ERR]，优先修复
   - 如果有 [WARN]，评估是否影响功能
   - 确保关键路径 ([OK]) 都通过

3. **更新文档**
   - 如新增模块，更新本说明
   - 如新增已知问题，添加到清单

### 升级前检查

在升级到新版本前，建议先运行：

```bash
# 1. 备份当前版本
git tag -a pre-upgrade-$(date +%Y%m%d) -m "升级前备份"

# 2. 运行健康检查
python health_check.py

# 3. 如检查通过，执行升级
# ... 升级步骤 ...

# 4. 升级后再次检查
python health_check.py
```

## 扩展健康检查

如需添加新的检查项，编辑 `health_check.py`：

1. 在 `run_all_checks()` 中添加检查调用
2. 实现新的检查方法（参考现有方法）
3. 使用 `CheckResult` 记录结果

示例：

```python
def _check_new_feature(self):
    print("[X/6] 检查新功能...")
    
    try:
        # 检查逻辑
        from my_module import my_function
        
        self.results.append(CheckResult(
            name="新功能",
            status="OK",
            message="新功能检查通过"
        ))
    except Exception as e:
        self.results.append(CheckResult(
            name="新功能",
            status="ERROR",
            message=f"新功能检查失败: {e}"
        ))
```

## 故障排查

### 健康检查本身报错

如果 `health_check.py` 运行失败：

1. **检查 Python 版本**
   ```bash
   python --version  # 需要 3.8+
   ```

2. **检查依赖**
   ```bash
   pip install pyyaml  # 如果缺少依赖
   ```

3. **手动检查**
   - 查看 `health_check.py` 的报错信息
   - 根据报错修复环境问题

### 特定检查项失败

参考各检查项的详细输出，常见问题：

- **类型检查失败**: 安装 pyright (`npm install -g pyright`)
- **配置文件失败**: 检查 config.yaml 格式
- **数据库失败**: 检查 wechat_monitor.db 是否存在且可读写
- **Web 应用失败**: 检查 Flask 是否安装 (`pip install flask`)
