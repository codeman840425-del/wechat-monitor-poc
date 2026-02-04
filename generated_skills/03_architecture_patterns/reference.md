# Reference: System Architecture and Design Patterns

> **Merged from**: `ARCHITECTURE.md`, `PHASE3_DESIGN.md`  
> **Focus**: Architecture, data flows, module design, extension patterns  
> **Generated**: 2026-02-03

---

## Table of Contents

1. [System Overview](#1-system-overview)
2. [Architecture Layers](#2-architecture-layers)
3. [Data Flow](#3-data-flow)
4. [Module Specifications](#4-module-specifications)
5. [Design Patterns](#5-design-patterns)
6. [Extension Guides](#6-extension-guides)
7. [Configuration System](#7-configuration-system)
8. [Performance Design](#8-performance-design)
9. [Security Architecture](#9-security-architecture)

---

## 1. System Overview

### 1.1 Purpose

wechat-monitor-poc is a **desktop application monitoring system** that:
- Captures chat messages via screenshot + OCR
- Matches keywords and stores to database
- Provides Web management interface

### 1.2 Technology Stack

| Layer | Technology |
|-------|------------|
| Backend | Python 3.9+, Flask |
| Database | SQLite3 |
| OCR | Tesseract-OCR + pytesseract |
| Screenshot | PIL/Pillow + Win32 API |
| Frontend | Bootstrap 5 + Jinja2 |
| Async | asyncio (notifications) |
| Real-time | Flask-SocketIO |

---

## 2. Architecture Layers

### 2.1 Layer Diagram

```
┌─────────────────────────────────────────────────────────────┐
│                        User Layer                            │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │ WeChat/QQ    │  │ Other Apps   │  │ Web Admin    │      │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘      │
└─────────┼─────────────────┼─────────────────┼──────────────┘
          │                 │                 │
          ▼                 ▼                 ▼
┌─────────────────────────────────────────────────────────────┐
│                     Message Source Layer                     │
│  ┌────────────────┐  ┌────────────────┐                     │
│  │ WeChatScreen   │  │ WindowScreen   │                     │
│  │ Source         │  │ Source         │                     │
│  └───────┬────────┘  └───────┬────────┘                     │
│          │                   │                              │
│          └─────────┬─────────┘                              │
│                    ▼                                        │
│           ┌────────────────┐                                │
│           │ BaseMessageSource│ (Abstract Base)              │
│           └───────┬────────┘                                │
└───────────────────┼─────────────────────────────────────────┘
                    │
                    ▼ poll()
┌─────────────────────────────────────────────────────────────┐
│                      Core Data Layer                         │
│           ┌────────────────┐                                │
│           │ ChatMessage    │ (Unified Format)               │
│           └───────┬────────┘                                │
└───────────────────┼─────────────────────────────────────────┘
                    │
                    ▼
┌─────────────────────────────────────────────────────────────┐
│                    Processing Layer                          │
│  ┌────────────────┐  ┌────────────────┐  ┌────────────────┐ │
│  │ KeywordFilter  │  │ MultiSource    │  │ Database       │ │
│  │ (Matching)     │  │ Monitor        │  │ Manager        │ │
│  └────────────────┘  └────────────────┘  └────────────────┘ │
└─────────────────────────────────────────────────────────────┘
                    │
                    ▼
┌─────────────────────────────────────────────────────────────┐
│                     Presentation Layer                       │
│  ┌────────────────┐  ┌────────────────┐  ┌────────────────┐ │
│  │ Dashboard      │  │ Messages       │  │ Keywords       │ │
│  │ (Statistics)   │  │ (History)      │  │ (Management)   │ │
│  └────────────────┘  └────────────────┘  └────────────────┘ │
└─────────────────────────────────────────────────────────────┘
```

### 2.2 Layer Responsibilities

**User Layer**:
- WeChat desktop application (monitored)
- QQ, DingTalk (extensible)
- Web browser (admin interface)

**Message Source Layer**:
- Abstract: `BaseMessageSource` (interface definition)
- Concrete: `WeChatScreenSource`, `WindowScreenSource`
- Output: `List[ChatMessage]`

**Core Data Layer**:
- Unified: `ChatMessage` dataclass
- Standardized format across all sources

**Processing Layer**:
- `MultiSourceMonitor`: Orchestrates multiple sources
- `KeywordFilter`: Pattern matching logic
- `DatabaseManager`: Persistence layer

**Presentation Layer**:
- Flask web application
- Dashboard, message list, keyword management
- REST API endpoints

---

## 3. Data Flow

### 3.1 High-Level Flow

```
Chat Window → Screenshot → OCR → Text Extraction → Keyword Match → Database → Web Display
```

### 3.2 Detailed Data Flow

**Step 1: Capture** (`WeChatScreenSource._capture_screenshot()`)
- Input: Window handle, capture region
- Process: PIL `ImageGrab.grab()` with bounding box
- Output: PIL Image object

**Step 2: OCR** (`WeChatScreenSource._recognize_text()`)
- Input: PIL Image
- Process: pytesseract `image_to_string()` with `chi_sim+eng`
- Output: Raw text string

**Step 3: Parse** (`WeChatScreenSource._parse_messages()`)
- Input: Raw OCR text
- Process: Text segmentation, metadata extraction
- Output: `List[ChatMessage]`

**Step 4: Match** (`KeywordFilter.check()`)
- Input: Message text, keyword list
- Process: Pattern matching (contain/exact/fuzzy)
- Output: Matched keyword or None

**Step 5: Store** (`DatabaseManager.insert_message()`)
- Input: `ChatMessage`, matched keyword
- Process: SQL INSERT with parameterized query
- Output: Database row ID

**Step 6: Display** (`web_app.py` routes)
- Input: Database query
- Process: Flask route → Template rendering
- Output: HTML/JSON response

### 3.3 Notification Flow (v0.5.0+)

```
Message Match → Notification Rule Engine → Channel Selection → Async Send
                              ↓
                    ┌─────────────────┐
                    │ DingTalk/WeCom  │
                    │ Email/Desktop   │
                    │ File/Console    │
                    └─────────────────┘
```

---

## 4. Module Specifications

### 4.1 Message Sources (`sources/`)

#### BaseMessageSource (`sources/base.py`)

```python
from abc import ABC, abstractmethod
from typing import List, Optional
from core.message import ChatMessage

class BaseMessageSource(ABC):
    """Abstract base for all message sources"""
    
    @abstractmethod
    def poll(self) -> List[ChatMessage]:
        """Fetch new messages from source"""
        pass
    
    @abstractmethod
    def is_available(self) -> bool:
        """Check if source is available"""
        pass
    
    def get_status(self) -> dict:
        """Get source status information"""
        return {"available": self.is_available()}
```

#### WeChatScreenSource (`sources/wechat_screen.py`)

**Core Methods**:
- `_find_window()`: Find WeChat window by title pattern
- `_capture_screenshot()`: Screenshot window region
- `_recognize_text()`: OCR with Tesseract
- `_parse_messages()`: Parse OCR text to ChatMessage objects

**Configuration**:
```python
window_title_pattern: str      # Window title regex
capture_region: Tuple[int, int, int, int]  # (offset_x, offset_y, width, height)
ocr_lang: str                  # "chi_sim+eng"
```

#### WindowScreenSource (`sources/window_screen.py`)

**Features**:
- Generic window capture
- `app_type` recognition (qq, dingtalk, etc.)
- Class name pattern matching
- Reuses WeChatScreenSource screenshot logic

### 4.2 Core Data (`core/`)

#### ChatMessage (`core/message.py`)

```python
from dataclasses import dataclass
from datetime import datetime
from typing import List, Optional

@dataclass
class ChatMessage:
    """Unified message format across all sources"""
    
    id: str                      # Unique identifier (UUID)
    platform: str                # Platform type: wechat_win, qq_win, etc.
    channel: str                 # Session/channel identifier
    sender: str                  # Sender name/display name
    content: str                 # Message text content
    timestamp: datetime          # Message timestamp
    matched_keywords: List[str]  # Keywords that matched
    
    def __post_init__(self):
        if not self.id:
            self.id = str(uuid.uuid4())
```

### 4.3 Processing Engine

#### MultiSourceMonitor (`monitor_v2.py`)

```python
class MultiSourceMonitor:
    """Multi-source message monitoring orchestrator"""
    
    def __init__(self, sources: List[BaseMessageSource], 
                 filter: KeywordFilter, db: DatabaseManager):
        self.sources = sources
        self.filter = filter
        self.db = db
        self.poll_interval = 5  # seconds
    
    def run(self):
        """Main monitoring loop"""
        while self.running:
            for source in self.sources:
                if source.is_available():
                    messages = source.poll()
                    self._process_messages(messages)
            time.sleep(self.poll_interval)
    
    def _process_messages(self, messages: List[ChatMessage]):
        """Process and store messages"""
        for msg in messages:
            matched = self.filter.check(msg.content)
            if matched:
                msg.matched_keywords.append(matched)
                self.db.insert_message(msg)
```

#### KeywordFilter (`monitor_v2.py`)

```python
class KeywordFilter:
    """Keyword matching with multiple modes"""
    
    MATCH_MODES = ["contain", "exact", "fuzzy"]
    
    def __init__(self, keywords: List[str], 
                 match_mode: str = "contain",
                 case_sensitive: bool = False):
        self.keywords = keywords
        self.match_mode = match_mode
        self.case_sensitive = case_sensitive
    
    def check(self, text: str) -> Optional[str]:
        """Check if text matches any keyword"""
        if not self.case_sensitive:
            text = text.lower()
        
        for keyword in self.keywords:
            kw = keyword if self.case_sensitive else keyword.lower()
            
            if self.match_mode == "contain":
                if kw in text:
                    return keyword
            elif self.match_mode == "exact":
                if kw == text:
                    return keyword
            elif self.match_mode == "fuzzy":
                if self._fuzzy_match(kw, text):
                    return keyword
        
        return None
```

### 4.4 Database Layer

#### DatabaseManager

**Messages Table**:
```sql
CREATE TABLE messages (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    window_title TEXT,
    message_text TEXT,
    matched_keyword TEXT,
    screenshot_path TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_messages_time ON messages(created_at);
CREATE INDEX idx_messages_keyword ON messages(matched_keyword);
```

**Keywords Table**:
```sql
CREATE TABLE keywords (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    word TEXT UNIQUE NOT NULL,
    enabled BOOLEAN DEFAULT 1,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

**Monitor Status Table**:
```sql
CREATE TABLE monitor_status (
    id INTEGER PRIMARY KEY,
    last_poll TIMESTAMP,
    messages_count INTEGER,
    status TEXT
);
```

### 4.5 Web Application (`web_app.py`)

#### Route Structure

```python
@app.route('/')
def dashboard():
    """Statistics dashboard"""
    stats = db.get_stats()
    return render_template('dashboard.html', stats=stats)

@app.route('/messages')
def messages():
    """Message list with filtering"""
    page = request.args.get('page', 1, type=int)
    keyword = request.args.get('keyword', '')
    messages = db.get_messages(page=page, keyword=keyword)
    return render_template('messages.html', messages=messages)

@app.route('/keywords', methods=['GET', 'POST'])
def keywords():
    """Keyword management (CRUD)"""
    if request.method == 'POST':
        # Add new keyword
        pass
    keywords = db.get_keywords()
    return render_template('keywords.html', keywords=keywords)

@app.route('/api/stats')
def api_stats():
    """Statistics API endpoint"""
    return jsonify(db.get_stats())
```

---

## 5. Design Patterns

### 5.1 Strategy Pattern (Message Sources)

**Context**: Different message sources need interchangeable implementations

```python
# Strategy interface
class BaseMessageSource(ABC):
    @abstractmethod
    def poll(self) -> List[ChatMessage]: pass

# Concrete strategies
class WeChatScreenSource(BaseMessageSource): ...
class WindowScreenSource(BaseMessageSource): ...
class DingTalkSource(BaseMessageSource): ...  # Future

# Usage
monitor = MultiSourceMonitor(
    sources=[WeChatScreenSource(), WindowScreenSource()],
    ...
)
```

### 5.2 Template Method Pattern (Processing)

**Context**: Define skeleton of monitoring algorithm, let subclasses customize steps

```python
class MultiSourceMonitor:
    def run(self):
        """Template method"""
        self.initialize()
        while self.running:
            for source in self.sources:
                if source.is_available():
                    messages = source.poll()
                    self.process_messages(messages)
            self.sleep_interval()
        self.cleanup()\n```

### 5.3 Repository Pattern (Database)

**Context**: Abstract data access, hide SQL details

```python
class DatabaseManager:
    """Repository for message data"""
    
    def insert_message(self, msg: ChatMessage) -> int:
        """Abstracts INSERT operation"""
        with self.connection() as conn:
            cursor = conn.execute(
                "INSERT INTO messages (...) VALUES (...)",
                (msg.window_title, msg.content, ...)
            )
            return cursor.lastrowid
    
    def get_messages(self, **filters) -> List[ChatMessage]:
        """Abstracts SELECT with filters"""
        # Build query based on filters
        # Return ChatMessage objects
```

### 5.4 Observer Pattern (Notifications)

**Context**: Message matching triggers multiple notification channels

```python
class NotificationSystem:
    def __init__(self):
        self.channels: Dict[str, NotificationChannel] = {}
    
    def register_channel(self, name: str, channel: NotificationChannel):
        self.channels[name] = channel
    
    async def notify(self, message: ChatMessage):
        """Notify all subscribed channels"""
        for name, channel in self.channels.items():
            await channel.send(message)
```

### 5.5 Factory Pattern (Config Loading)

**Context**: Create configuration from different sources (YAML, DB)

```python
class ConfigFactory:
    @staticmethod
    def from_yaml(path: str) -> Config:
        with open(path) as f:
            return Config(yaml.safe_load(f))
    
    @staticmethod
    def from_database(db: DatabaseManager) -> Config:
        return Config(db.get_config())
```

---

## 6. Extension Guides

### 6.1 Adding a New Message Source

**Step 1**: Create `sources/new_source.py`

```python
from typing import List, Optional
from sources.base import BaseMessageSource
from core.message import ChatMessage

class NewSource(BaseMessageSource):
    """New message source implementation"""
    
    def __init__(self, config: dict):
        super().__init__()
        self.config = config
        self._init_connection()
    
    def _init_connection(self):
        """Initialize connection to source"""
        pass
    
    def poll(self) -> List[ChatMessage]:
        """Fetch new messages"""
        messages = []
        # Implementation: connect, fetch, parse
        raw_data = self._fetch_data()
        for item in raw_data:
            msg = self._parse_to_message(item)
            messages.append(msg)
        return messages
    
    def is_available(self) -> bool:
        """Check if source is ready"""
        try:
            # Test connection
            return True
        except:
            return False
```

**Step 2**: Register in `monitor_v2.py`

```python
from sources.new_source import NewSource

def create_monitor():
    sources = [
        WeChatScreenSource(wechat_config),
        WindowScreenSource(generic_config),
        NewSource(new_config),  # Add new source
    ]
    return MultiSourceMonitor(sources, ...)
```

**Step 3**: Update configuration

```yaml
# config.yaml
sources:
  new_source:
    enabled: true
    connection_string: "..."
```

### 6.2 Adding a New Web Route

**Step 1**: Add route handler in `web_app.py`

```python
@app.route('/new-feature')
def new_feature():
    """New feature page"""
    data = db.get_new_feature_data()
    return render_template('new_feature.html', data=data)

@app.route('/api/new-feature')
def api_new_feature():
    """API endpoint for new feature"""
    data = db.get_new_feature_data()
    return jsonify(data)
```

**Step 2**: Create template `templates/new_feature.html`

```html
{% extends "base.html" %}
{% block content %}
  <h1>New Feature</h1>
  <!-- Feature content -->
{% endblock %}
```

### 6.3 Adding Keyword Match Modes

**Step 1**: Modify `KeywordFilter`

```python
class KeywordFilter:
    MATCH_MODES = ["contain", "exact", "fuzzy", "regex"]
    
    def check(self, text: str) -> Optional[str]:
        if self.match_mode == "regex":
            return self._regex_match(text)
        # ... existing modes
    
    def _regex_match(self, text: str) -> Optional[str]:
        import re
        for pattern in self.keywords:
            if re.search(pattern, text, re.IGNORECASE):
                return pattern
        return None
```

**Step 2**: Update config schema

```yaml
keywords:
  match_mode: "regex"  # New option
  patterns:
    - "退款|退钱"
    - "订单.*投诉"
```

---

## 7. Configuration System

### 7.1 Configuration Hierarchy

**Priority** (highest to lowest):
1. Database configuration (runtime, dynamic)
2. `config.yaml` file (persistent)
3. Code defaults (fallback)

### 7.2 Complete Config Schema

```yaml
# ==================== Database ====================
database:
  db_path: "./wechat_monitor.db"
  data_retention_days: 90
  enable_vacuum: true

# ==================== Monitoring ====================
monitor:
  interval: 5                    # Poll interval (seconds)
  target_window_title: ""        # Window title pattern (partial match)
  
  screenshot:
    save_screenshots: true
    save_directory: "./screenshots"
    retention_days: 7
    quality: 85                  # JPEG quality

# ==================== OCR ====================
ocr:
  tesseract_cmd: ""              # Custom path (empty = system PATH)
  lang: "chi_sim+eng"           # Language pack
  config: "--oem 3 --psm 6"     # Tesseract config string
  
  preprocess:
    enabled: true
    scale: 2.0                   # Image scale factor
    contrast: false
    sharpen: false
  
  chat_area:                     # Crop region (relative 0-1)
    left_crop: 0.28
    top_crop: 0.09
    right_crop: 0.03
    bottom_crop: 0.14

# ==================== Keywords ====================
keywords:
  list:
    - "付款"
    - "订单"
    - "投诉"
  match_mode: "contain"          # contain|exact|fuzzy
  case_sensitive: false
  fuzzy_threshold: 0.7

# ==================== Logging ====================
logging:
  level: "INFO"                  # DEBUG|INFO|WARNING|ERROR
  log_file: "./monitor.log"
  console_output: true
  max_size_mb: 50
  backup_count: 5

# ==================== Notification ====================
notification:
  enabled: true
  
  rules:
    - name: "Critical Alerts"
      keywords: ["投诉", "纠纷"]
      channels: ["dingtalk", "email"]
      priority: "CRITICAL"
      cooldown: 300                # Seconds
  
  channels:
    dingtalk:
      enabled: false
      webhook_url: "https://..."
      secret: ""
    
    email:
      enabled: false
      smtp_server: "smtp.qq.com"
      smtp_port: 587
      username: ""
      password: ""
```

### 7.3 Configuration Validation

```python
def validate_config(config: dict) -> List[str]:
    """Validate configuration and return error messages"""
    errors = []
    
    # Required sections
    required = ['database', 'monitor', 'keywords']
    for section in required:
        if section not in config:
            errors.append(f"Missing required section: {section}")
    
    # Type validation
    if not isinstance(config.get('monitor', {}).get('interval'), (int, float)):
        errors.append("monitor.interval must be a number")
    
    # Range validation
    interval = config.get('monitor', {}).get('interval', 0)
    if interval < 1 or interval > 3600:
        errors.append("monitor.interval must be between 1 and 3600")
    
    return errors
```

---

## 8. Performance Design

### 8.1 Screenshot Optimization

**Region Cropping**:
- Only capture chat area, exclude contact list and input box
- Config: `ocr.chat_area` crop percentages
- Reduces OCR processing time by ~50%

**Change Detection**:
- Perceptual hash comparison of consecutive screenshots
- Skip OCR if hash similarity > threshold
- Config: `advanced.deduplication.enabled`

**Preprocessing**:
- Scale image 2x for better OCR accuracy
- Disable contrast/sharpen (often degrades text)
- Config: `ocr.preprocess.scale = 2.0`

### 8.2 Database Optimization

**Indexes**:
```sql
CREATE INDEX idx_messages_time ON messages(created_at);
CREATE INDEX idx_messages_keyword ON messages(matched_keyword);
CREATE INDEX idx_messages_window ON messages(window_title);
```

**Pagination**:
```python
def get_messages(self, page: int = 1, per_page: int = 20):
    offset = (page - 1) * per_page
    query = """
        SELECT * FROM messages 
        ORDER BY created_at DESC 
        LIMIT ? OFFSET ?
    """
    return self.execute(query, (per_page, offset))
```

**Cleanup**:
```python
def cleanup_old_data(self, retention_days: int):
    """Delete old messages and screenshots"""
    cutoff = datetime.now() - timedelta(days=retention_days)
    
    # Delete old messages
    self.execute("DELETE FROM messages WHERE created_at < ?", (cutoff,))
    
    # Delete old screenshots
    for screenshot in screenshot_dir.glob("*.png"):
        if screenshot.stat().st_mtime < cutoff.timestamp():
            screenshot.unlink()
```

### 8.3 Polling Optimization

**Concurrent Sources**:
```python
import asyncio

async def poll_all_sources(sources: List[BaseMessageSource]):
    """Poll all sources concurrently"""
    tasks = [source.poll_async() for source in sources]
    results = await asyncio.gather(*tasks, return_exceptions=True)
    return results
```

**Adjustable Interval**:
- Fast: 5 seconds (real-time monitoring)
- Normal: 10 seconds (balanced)
- Slow: 30-60 seconds (low resource usage)

---

## 9. Security Architecture

### 9.1 Data Security

**Local Storage**:
- SQLite database: Local file, no network exposure
- Screenshots: Local directory, regular cleanup
- Logs: Local files, rotation enabled

**Sensitive Data Handling**:
```python
def mask_sensitive_data(text: str) -> str:
    """Mask PII patterns in OCR results"""
    import re
    
    # ID numbers
    text = re.sub(r'\d{17}[\dXx]', '***ID***', text)
    
    # Phone numbers
    text = re.sub(r'1[3-9]\d{9}', '***PHONE***', text)
    
    return text
```

### 9.2 Code Security

**SQL Injection Prevention**:
```python
# CORRECT: Parameterized queries
cursor.execute(
    "SELECT * FROM messages WHERE matched_keyword = ?",
    (keyword,)
)

# WRONG: String formatting (NEVER DO THIS)
cursor.execute(f"SELECT * FROM messages WHERE matched_keyword = '{keyword}'")
```

**Path Traversal Prevention**:
```python
import os
from pathlib import Path

def safe_save_screenshot(image, filename: str) -> Path:
    """Save screenshot with path validation"""
    base_dir = Path(config['monitor']['screenshot']['save_directory'])
    
    # Resolve to absolute path
    target = (base_dir / filename).resolve()
    
    # Ensure path is within allowed directory
    if not str(target).startswith(str(base_dir.resolve())):
        raise ValueError("Path traversal attempt detected")
    
    return target
```

**XSS Prevention (Flask)**:
```html
<!-- Jinja2 auto-escapes by default -->
<p>{{ message.content }}</p>  <!-- Safe: auto-escaped -->

<p>{{ message.content|safe }}</p>  <!-- Dangerous: raw HTML -->
```

### 9.3 Configuration Security

**Environment Variables**:
```python
import os

# CORRECT: From environment
api_key = os.environ.get('WECHAT_API_KEY')
if not api_key:
    raise ValueError("WECHAT_API_KEY not set")

# WRONG: Hardcoded (FORBIDDEN)
api_key = "wx1234567890abcdef"
```

**Secrets in Config**:
```yaml
# CORRECT: Empty or env reference
api:
  app_id: ""  # Set via WECHAT_APP_ID env var
  secret: ""  # Set via WECHAT_SECRET env var
```

### 9.4 Security Checklist

- [ ] No hardcoded API keys or passwords
- [ ] No absolute paths with real usernames
- [ ] Parameterized SQL queries
- [ ] Path validation for file operations
- [ ] Template escaping for user content
- [ ] Input validation on API endpoints
- [ ] Environment variables for secrets
- [ ] Regular security scans: `health_check.py --security`

---

**End of Reference Documentation**
