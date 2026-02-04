# WeChat 消息监控 PoC 项目

## 项目说明
这是一个基于 Windows UI Automation 技术的微信消息监控概念验证项目。

## 技术栈
- Python 3.8+
- uiautomation (Windows UI Automation 库)

## 当前限制（阶段1 PoC）
1. 只能读取当前可见的聊天窗口消息
2. 需要手动选择要监控的窗口
3. 无法区分消息的发送者和接收者
4. 无法自动检测新消息（需要重新运行脚本）
5. 微信版本更新可能导致UI结构变化，需要调整代码

## 文件说明
- `requirements.txt` - Python 依赖包列表
- `wechat_poc.py` - 主程序，实现窗口枚举和消息读取
- `README.md` - 项目说明文档

## 安装和运行步骤

### 1. 安装 Python 依赖
```bash
pip install -r requirements.txt
```

### 2. 确保微信已登录并打开
- 在 Windows 桌面上登录微信
- 打开一个聊天窗口（好友或群聊）
- 确保能看到聊天记录

### 3. 运行 PoC 脚本
```bash
python wechat_poc.py
```

### 4. 按照提示操作
- 脚本会列出所有微信窗口
- 输入编号选择要读取的聊天窗口
- 查看终端输出的消息内容

## 注意事项
- 本项目仅供技术学习和验证使用
- 使用时应遵守相关法律法规和微信用户协议
- 仅用于监控工作微信账号，且需事先获得相关人员同意
