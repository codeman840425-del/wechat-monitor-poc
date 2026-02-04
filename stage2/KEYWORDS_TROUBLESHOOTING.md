# 关键字加载问题排查指南

## 问题现象
- 在 Web 界面 /keywords 添加了新关键字（如"异常"）
- 但监控程序启动日志中没有显示这个新关键字
- 或者包含新关键字的消息被标记为"未匹配"

## 快速诊断

运行诊断脚本：
```bash
python diagnose_keywords.py
```

这个脚本会显示：
1. 数据库中所有关键字
2. 哪些关键字是启用的
3. 匹配测试

## 常见原因和解决方案

### 原因 1：运行的是旧版监控程序

**检查方法**：
```bash
# 检查你运行的是哪个文件
ps aux | grep python
```

**解决方案**：
- 使用新版监控程序：`python monitor_v2.py`
- 旧版 `monitor.py` 也支持数据库加载，但 `monitor_v2.py` 是推荐版本

### 原因 2：数据库中没有保存新关键字

**检查方法**：
```bash
python -c "
from database import DatabaseManager
db = DatabaseManager('./wechat_monitor.db')
keywords = db.get_keywords_from_db(enabled_only=True)
print('数据库关键字:', keywords)
"
```

**解决方案**：
- 在 Web 界面重新添加关键字
- 检查浏览器控制台是否有报错
- 检查 web_app.py 日志是否有错误

### 原因 3：关键字被禁用

**检查方法**：
在 Web 界面的 /keywords 页面，检查新关键字的状态是否为"已启用"

**解决方案**：
- 点击关键字旁边的"启用"按钮

### 原因 4：匹配逻辑问题

**检查方法**：
```bash
python -c "
from database import DatabaseManager
from monitor_v2 import KeywordFilter

db = DatabaseManager('./wechat_monitor.db')
keywords = db.get_keywords_from_db(enabled_only=True)
print('关键字列表:', keywords)

kf = KeywordFilter(keywords, case_sensitive=False)
test_msg = '这里包含异常关键词'
result = kf.check(test_msg)
print(f'测试结果: {result}')
"
```

**解决方案**：
- 确保关键字是纯文本，不包含特殊字符
- 检查是否区分大小写（默认不区分）

## 验证步骤

1. **确认数据库中有新关键字**：
   ```bash
   python diagnose_keywords.py
   ```

2. **启动监控程序并查看日志**：
   ```bash
   python monitor_v2.py
   ```
   观察启动日志中的"从数据库加载 X 个关键字"和"关键字过滤器初始化完成"两行

3. **测试匹配**：
   - 发送包含新关键字的消息
   - 检查 monitor.log 中是否正确匹配

## 如果问题仍然存在

请提供以下信息：
1. `python diagnose_keywords.py` 的完整输出
2. 监控程序启动日志（前 20 行）
3. 你添加的新关键字是什么
4. 测试的消息内容是什么
