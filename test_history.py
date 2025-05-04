import os
import json
import logging
from history_manager import HistoryManager

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('test_history.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

def test_history_saving():
    try:
        # Создаем экземпляр HistoryManager
        logger.info("Creating HistoryManager instance")
        history_manager = HistoryManager()
        
        # Тестовые данные
        test_user_id = 1
        test_filename = "test_file.txt"
        test_params = {
            "min_word_length": 5,
            "start_date": "2024-01-01",
            "end_date": "2024-03-20"
        }
        
        # Проверяем сохранение истории
        logger.info(f"Testing save_user_history for user {test_user_id}")
        history_id = history_manager.save_user_history(test_user_id, test_filename, test_params)
        
        if not history_id:
            logger.error("Failed to save history - history_id is None")
            return
            
        logger.info(f"Successfully saved history with ID: {history_id}")
        
        # Проверяем, что файл создался
        history_file = os.path.join(history_manager.history_dir, f"history_{test_user_id}.json")
        if not os.path.exists(history_file):
            logger.error(f"History file was not created: {history_file}")
            return
            
        logger.info(f"History file exists: {history_file}")
        
        # Проверяем содержимое файла
        try:
            with open(history_file, "r", encoding="utf-8") as f:
                content = f.read().strip()
                logger.info(f"File content: {content}")
                history = json.loads(content)
                logger.info(f"Loaded history items: {len(history)}")
                logger.info(f"History content: {history}")
        except Exception as e:
            logger.error(f"Error reading history file: {str(e)}")
            return
            
        # Проверяем загрузку истории
        loaded_history = history_manager.load_user_history(test_user_id)
        logger.info(f"Loaded history items: {len(loaded_history)}")
        logger.info(f"History content: {loaded_history}")
        
    except Exception as e:
        logger.error(f"Error during testing: {str(e)}")

if __name__ == "__main__":
    test_history_saving() 