"""
对话历史管理服务
支持对话的存储、检索、删除和摘要生成
"""

from typing import List, Dict, Any, Optional
from datetime import datetime
import json
import logging
from pathlib import Path

logger = logging.getLogger(__name__)


class ConversationService:
    """对话历史管理服务"""
    
    def __init__(self, storage_path: str = None):
        """
        初始化对话服务
        
        Args:
            storage_path: 对话历史存储路径（默认使用内存存储）
        """
        self.storage_path = storage_path
        # 使用内存存储（生产环境应使用数据库）
        self.conversations: Dict[str, Dict] = {}
        
        if storage_path:
            Path(storage_path).mkdir(parents=True, exist_ok=True)
            self._load_from_disk()
    
    def create_conversation(
        self, 
        user_id: str, 
        title: str = None,
        session_id: str = None
    ) -> Dict[str, Any]:
        """
        创建新对话
        
        Args:
            user_id: 用户ID
            title: 对话标题（可选）
            session_id: 会话ID（可选，如不提供则自动生成）
        
        Returns:
            对话信息
        """
        import uuid
        
        if not session_id:
            session_id = f"conv_{uuid.uuid4().hex[:16]}"
        
        conversation = {
            "session_id": session_id,
            "user_id": user_id,
            "title": title or "新对话",
            "messages": [],
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat(),
            "metadata": {
                "message_count": 0,
                "last_question": None
            }
        }
        
        self.conversations[session_id] = conversation
        self._save_to_disk()
        
        logger.info(f"Created conversation: {session_id}")
        return conversation
    
    def add_message(
        self,
        session_id: str,
        role: str,
        content: str,
        metadata: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """
        向对话添加消息
        
        Args:
            session_id: 会话ID
            role: 角色（user/ai）
            content: 消息内容
            metadata: 额外元数据（sources, reasoning_trace等）
        
        Returns:
            更新后的对话
        """
        if session_id not in self.conversations:
            # 自动创建对话
            self.conversations[session_id] = {
                "session_id": session_id,
                "user_id": "anonymous",
                "title": "新对话",
                "messages": [],
                "created_at": datetime.now().isoformat(),
                "updated_at": datetime.now().isoformat(),
                "metadata": {"message_count": 0}
            }
        
        conversation = self.conversations[session_id]
        
        message = {
            "role": role,
            "content": content,
            "timestamp": datetime.now().isoformat(),
            "metadata": metadata or {}
        }
        
        conversation["messages"].append(message)
        conversation["updated_at"] = datetime.now().isoformat()
        conversation["metadata"]["message_count"] = len(conversation["messages"])
        
        # 更新标题（使用第一个用户问题）
        if role == "user" and conversation["metadata"]["message_count"] <= 2:
            # 截断过长的标题
            title = content[:30] + "..." if len(content) > 30 else content
            conversation["title"] = title
            conversation["metadata"]["last_question"] = content
        
        self._save_to_disk()
        
        logger.info(f"Added {role} message to conversation {session_id}")
        return conversation
    
    def get_conversation(self, session_id: str) -> Optional[Dict[str, Any]]:
        """获取对话详情"""
        return self.conversations.get(session_id)
    
    def get_conversation_messages(
        self,
        session_id: str,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """
        获取对话消息列表
        
        Args:
            session_id: 会话ID
            limit: 返回最近N条消息
        
        Returns:
            消息列表
        """
        conversation = self.conversations.get(session_id)
        if not conversation:
            return []
        
        messages = conversation.get("messages", [])
        return messages[-limit:] if limit else messages
    
    def list_conversations(
        self,
        user_id: str = None,
        limit: int = 50,
        offset: int = 0
    ) -> List[Dict[str, Any]]:
        """
        列出对话列表
        
        Args:
            user_id: 用户ID（可选，筛选特定用户的对话）
            limit: 返回数量
            offset: 偏移量
        
        Returns:
            对话列表（按更新时间倒序）
        """
        conversations = list(self.conversations.values())
        
        # 筛选用户
        if user_id:
            conversations = [c for c in conversations if c["user_id"] == user_id]
        
        # 按更新时间排序
        conversations.sort(key=lambda x: x["updated_at"], reverse=True)
        
        # 分页
        return conversations[offset:offset + limit]
    
    def delete_conversation(self, session_id: str) -> bool:
        """
        删除对话
        
        Args:
            session_id: 会话ID
        
        Returns:
            是否删除成功
        """
        if session_id in self.conversations:
            del self.conversations[session_id]
            self._save_to_disk()
            logger.info(f"Deleted conversation: {session_id}")
            return True
        return False
    
    def clear_user_conversations(self, user_id: str) -> int:
        """
        清空用户的所有对话
        
        Args:
            user_id: 用户ID
        
        Returns:
            删除的对话数量
        """
        to_delete = [
            sid for sid, conv in self.conversations.items()
            if conv["user_id"] == user_id
        ]
        
        for session_id in to_delete:
            del self.conversations[session_id]
        
        self._save_to_disk()
        logger.info(f"Cleared {len(to_delete)} conversations for user {user_id}")
        return len(to_delete)
    
    def generate_summary(self, session_id: str) -> str:
        """
        生成对话摘要
        
        Args:
            session_id: 会话ID
        
        Returns:
            对话摘要
        """
        conversation = self.conversations.get(session_id)
        if not conversation:
            return ""
        
        messages = conversation.get("messages", [])
        if not messages:
            return "空对话"
        
        # 简单摘要：第一个问题 + 消息数量
        user_messages = [m for m in messages if m["role"] == "user"]
        
        if user_messages:
            first_question = user_messages[0]["content"][:50]
            summary = f"{first_question}... ({len(messages)} 条消息)"
        else:
            summary = f"对话 ({len(messages)} 条消息)"
        
        return summary
    
    def get_conversation_context(
        self,
        session_id: str,
        max_turns: int = 5
    ) -> List[Dict[str, str]]:
        """
        获取对话上下文（用于传递给 AI）
        
        Args:
            session_id: 会话ID
            max_turns: 最多保留几轮对话
        
        Returns:
            对话历史列表
        """
        messages = self.get_conversation_messages(session_id)
        
        # 只保留最近N轮对话
        recent_messages = messages[-(max_turns * 2):] if max_turns else messages
        
        # 格式化为简洁的上下文
        context = []
        for msg in recent_messages:
            context.append({
                "role": msg["role"],
                "content": msg["content"]
            })
        
        return context
    
    def _save_to_disk(self):
        """保存到磁盘（可选）"""
        if not self.storage_path:
            return
        
        try:
            file_path = Path(self.storage_path) / "conversations.json"
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(self.conversations, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.error(f"Failed to save conversations: {e}")
    
    def _load_from_disk(self):
        """从磁盘加载（可选）"""
        if not self.storage_path:
            return
        
        try:
            file_path = Path(self.storage_path) / "conversations.json"
            if file_path.exists():
                with open(file_path, 'r', encoding='utf-8') as f:
                    self.conversations = json.load(f)
                logger.info(f"Loaded {len(self.conversations)} conversations from disk")
        except Exception as e:
            logger.error(f"Failed to load conversations: {e}")


# 全局单例
conversation_service = ConversationService(storage_path="./storage/conversations")

