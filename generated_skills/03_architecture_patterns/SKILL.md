# Architecture Patterns - System Design

---
skill_id: architecture-patterns
trigger_keywords: ["architecture", "design", "module", "data flow"]
dependencies: ["skill-system"]
---

## System Layers
```
User → Source → Core → Processing → Presentation
```

**Data Flow**: Chat → Screenshot → OCR → Parse → Match → DB → Web

## Key Modules

### Message Sources (`sources/`)
- `BaseMessageSource`: Interface
- `WeChatScreenSource`: WeChat OCR
- `WindowScreenSource`: Generic capture
- **Add new**: Inherit `BaseMessageSource`, implement `poll()`

### Core Data (`core/`)
```python
@dataclass
class ChatMessage:
    id: str; platform: str; content: str
    timestamp: datetime; matched_keywords: List[str]
```

### Processing (`monitor_v2.py`)
- `MultiSourceMonitor`: Orchestrates sources
- `KeywordFilter`: Modes = contain|exact|fuzzy

### Web (`web_app.py`)
Routes: `/` (dashboard), `/messages`, `/keywords`, `/api/*`

## Extension Patterns

### New Message Source
```python
class NewSource(BaseMessageSource):
    def poll(self) -> List[ChatMessage]: ...
```

### New Web Route
```python
@app.route('/new')
def new(): return render_template('new.html')
```

## Config Priority
1. Database (runtime) - Highest
2. `config.yaml` (file)
3. Code defaults

## Design Patterns
- **Strategy**: Message sources
- **Template**: Processing flow
- **Repository**: Database layer
- **Observer**: Notifications

## See reference.md For
- Complete architecture
- Database schemas
- Performance optimization
- Security architecture
