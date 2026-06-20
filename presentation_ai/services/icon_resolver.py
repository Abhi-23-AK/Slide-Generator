# services/icon_resolver.py

TOPIC_EMOJI_MAP = {
  # Technology & AI
  "ai": "🤖", "artificial intelligence": "🤖",
  "machine learning": "🧠", "deep learning": "🧠",
  "robot": "🤖", "automation": "⚙️",
  "neural network": "🔮", "algorithm": "🔢",
  
  # Data & Analytics
  "data": "📊", "analytics": "📊", "analysis": "📈",
  "pandas": "📊", "dataframe": "🗂️",
  "matplotlib": "📈", "visualization": "📊",
  "statistics": "📉", "chart": "📊", "graph": "📈",
  "database": "🗄️", "sql": "🗄️",
  
  # Programming & Dev
  "python": "🐍", "javascript": "💛", "code": "💻",
  "programming": "💻", "software": "🖥️",
  "api": "🔌", "backend": "⚙️", "frontend": "🎨",
  "web": "🌐", "mobile": "📱", "app": "📱",
  "cloud": "☁️", "server": "🖧", "docker": "🐳",
  "git": "🔀", "testing": "🧪", "debug": "🐛",
  
  # Business & Finance
  "business": "💼", "strategy": "♟️",
  "revenue": "💰", "profit": "💵", "finance": "💳",
  "marketing": "📣", "sales": "📦", "growth": "📈",
  "startup": "🚀", "entrepreneur": "💡",
  "investment": "💹", "budget": "💰",
  "goals": "🎯", "target": "🎯",
  
  # Education & Research
  "summary": "📋", "overview": "🔍",
  "introduction": "👋", "conclusion": "✅",
  "research": "🔬", "study": "📚",
  "education": "🎓", "learning": "📖",
  "theory": "💡", "concept": "💡",
  "history": "📜", "timeline": "⏳",
  
  # Science & Health
  "health": "❤️", "medical": "🏥",
  "biology": "🧬", "chemistry": "⚗️",
  "physics": "⚛️", "environment": "🌱",
  "climate": "🌍", "energy": "⚡",
  "space": "🌌", "rocket": "🚀",
  
  # Communication & Social
  "team": "👥", "people": "👤",
  "communication": "💬", "social": "🌐",
  "network": "🕸️", "community": "🤝",
  "culture": "🎭", "diversity": "🌈",
  
  # Process & Management
  "process": "⚙️", "workflow": "🔄",
  "management": "📋", "planning": "🗓️",
  "roadmap": "🗺️", "milestone": "🏁",
  "architecture": "🏗️", "structure": "🏛️",
  "security": "🔒", "privacy": "🛡️",
  
  # Creative
  "design": "🎨", "creative": "✨",
  "innovation": "💡", "idea": "💡",
  "art": "🎨", "music": "🎵",
  
  # Default fallbacks
  "introduction": "📌", "agenda": "📋",
  "features": "⭐", "benefits": "✨",
  "challenges": "⚠️", "solution": "✅",
  "comparison": "⚖️", "review": "🔍",
  "next steps": "➡️", "future": "🔮",
  "questions": "❓", "contact": "📧",
  "thank you": "🙏", "about": "ℹ️",
}

# Default emoji when no match found
DEFAULT_EMOJI = "📌"

def resolve_icon_emoji(keyword: str) -> str:
    """
    Given a keyword or slide title, returns the best emoji.
    Priority: exact match -> partial match -> reverse partial -> default
    """
    if not keyword:
        return DEFAULT_EMOJI
    
    keyword_lower = keyword.lower().strip()
    
    # 1. Exact match
    if keyword_lower in TOPIC_EMOJI_MAP:
        return TOPIC_EMOJI_MAP[keyword_lower]
    
    # 2. Partial match — check if any key is in the keyword
    for key, emoji in TOPIC_EMOJI_MAP.items():
        if key in keyword_lower:
            return emoji
    
    # 3. Reverse partial — check if keyword is in any key
    for key, emoji in TOPIC_EMOJI_MAP.items():
        if keyword_lower in key:
            return emoji
    
    # 4. Default fallback
    return DEFAULT_EMOJI
