import json
import os
from datetime import datetime
import uuid
import logging
from typing import Optional, Dict, Any, List

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('history/history.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class HistoryManager:
    _instance = None
    _initialized = False

    def __new__(cls, history_dir: str = None):
        if cls._instance is None:
            cls._instance = super(HistoryManager, cls).__new__(cls)
        return cls._instance

    def __init__(self, history_dir: str = None):
        if self._initialized:
            return
            
        self._initialized = True
        
        if history_dir is None:
            # Используем абсолютный путь к директории проекта
            base_dir = os.path.dirname(os.path.abspath(__file__))
            history_dir = os.path.join(base_dir, "history")
            
        self.history_dir = os.path.abspath(history_dir)
        logger.info(f"Initializing HistoryManager with directory: {self.history_dir}")
        logger.info(f"Current working directory: {os.getcwd()}")
        
        # Проверяем, что директория существует и доступна для записи
        if not os.path.exists(self.history_dir):
            logger.error(f"History directory does not exist: {self.history_dir}")
            logger.error("Please run init_history.py first")
            raise FileNotFoundError(f"History directory does not exist: {self.history_dir}")
            
        # Проверяем права на запись
        test_file = os.path.join(self.history_dir, "test_write.tmp")
        try:
            with open(test_file, "w") as f:
                f.write("test")
            os.remove(test_file)
            logger.info(f"Write access confirmed for directory: {self.history_dir}")
        except Exception as e:
            logger.error(f"No write access to directory: {self.history_dir}")
            logger.error(f"Error details: {str(e)}")
            raise PermissionError(f"No write access to directory: {self.history_dir}")

    def save_user_history(self, user_id: int, filename: str, params: dict = None) -> str:
        """Сохраняет историю генерации для пользователя"""
        try:
            logger.info(f"Starting save_user_history for user {user_id}, file {filename}")
            logger.info(f"Parameters: {params}")
            
            # Формируем путь к файлу истории пользователя
            history_file = os.path.join(self.history_dir, f"history_{user_id}.json")
            logger.info(f"History file path: {history_file}")
            
            # Создаем новую запись
            history_item = {
                "id": str(uuid.uuid4()),
                "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "filename": filename,
                "params": params
            }
            logger.info(f"Created history item: {history_item}")
            
            # Загружаем существующую историю или создаем новый список
            history = []
            if os.path.exists(history_file):
                try:
                    with open(history_file, "r", encoding="utf-8") as f:
                        content = f.read().strip()
                        logger.info(f"Read content from file: {content}")
                        if content:
                            history = json.loads(content)
                            logger.info(f"Loaded existing history with {len(history)} items")
                        else:
                            logger.info("File is empty, starting with empty list")
                except json.JSONDecodeError as e:
                    logger.error(f"JSON decode error: {str(e)}")
                    history = []
                except Exception as e:
                    logger.error(f"Error reading history file: {str(e)}")
                    history = []
            else:
                logger.info("History file does not exist, starting with empty list")
            
            # Добавляем новую запись
            history.append(history_item)
            logger.info(f"Added new item to history, total items: {len(history)}")
            
            # Сохраняем обновленную историю
            try:
                with open(history_file, "w", encoding="utf-8") as f:
                    json.dump(history, f, ensure_ascii=False, indent=2)
                logger.info(f"Successfully saved history to {history_file}")
                
                # Проверяем, что файл действительно записался
                with open(history_file, "r", encoding="utf-8") as f:
                    saved_content = f.read().strip()
                    logger.info(f"Verified saved content: {saved_content}")
                
                return history_item["id"]
            except Exception as e:
                logger.error(f"Error writing to history file: {str(e)}")
                return None
            
        except Exception as e:
            logger.error(f"Error in save_user_history: {str(e)}")
            return None

    def load_user_history(self, user_id: int) -> List[Dict[str, Any]]:
        """Загружает историю генераций пользователя"""
        try:
            logger.info(f"Loading history for user {user_id}")
            history_file = os.path.join(self.history_dir, f"history_{user_id}.json")
            logger.info(f"History file path: {history_file}")
            
            if not os.path.exists(history_file):
                logger.info(f"History file does not exist for user {user_id}")
                return []
            
            with open(history_file, "r", encoding="utf-8") as f:
                content = f.read().strip()
                logger.info(f"Read content: {content}")
                if content:
                    history = json.loads(content)
                    logger.info(f"Loaded {len(history)} history items")
                    return history
                else:
                    logger.info("File is empty")
                    return []
        except Exception as e:
            logger.error(f"Error loading history: {str(e)}")
            return []

    def get_history_item(self, user_id: int, history_id: str) -> Optional[Dict[str, Any]]:
        """Получает конкретный элемент истории пользователя"""
        try:
            logger.info(f"Getting history item {history_id} for user {user_id}")
            history = self.load_user_history(user_id)
            
            for item in history:
                if item["id"] == history_id:
                    logger.info(f"Found history item: {item}")
                    return item
                    
            logger.warning(f"History item {history_id} not found")
            return None
            
        except Exception as e:
            logger.error(f"Error getting history item: {str(e)}")
            return None

    def delete_history_item(self, user_id: int, history_id: str) -> bool:
        """Удаляет элемент истории пользователя"""
        try:
            logger.info(f"Deleting history item {history_id} for user {user_id}")
            history_file = os.path.join(self.history_dir, f"history_{user_id}.json")
            
            if not os.path.exists(history_file):
                logger.warning(f"History file does not exist for user {user_id}")
                return False
            
            with open(history_file, "r", encoding="utf-8") as f:
                history = json.load(f)
            
            # Фильтруем историю, исключая удаляемый элемент
            original_length = len(history)
            history = [item for item in history if item["id"] != history_id]
            
            if len(history) == original_length:
                logger.warning(f"History item {history_id} not found")
                return False
            
            # Сохраняем обновленную историю
            with open(history_file, "w", encoding="utf-8") as f:
                json.dump(history, f, ensure_ascii=False, indent=2)
            logger.info(f"Successfully deleted history item {history_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error deleting history item: {str(e)}")
            return False 