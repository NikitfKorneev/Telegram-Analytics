import os
import logging
import json

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

def init_history_directory():
    try:
        # Получаем абсолютный путь к директории проекта
        base_dir = os.path.dirname(os.path.abspath(__file__))
        history_dir = os.path.join(base_dir, "history")
        logger.info(f"Base directory: {base_dir}")
        logger.info(f"History directory: {history_dir}")
        
        # Создаем директорию history, если она не существует
        if not os.path.exists(history_dir):
            os.makedirs(history_dir, exist_ok=True)
            logger.info(f"Created history directory: {history_dir}")
        else:
            logger.info(f"History directory already exists: {history_dir}")
            
        # Проверяем права на запись
        test_file = os.path.join(history_dir, "test_write.tmp")
        try:
            with open(test_file, "w") as f:
                f.write("test")
            os.remove(test_file)
            logger.info(f"Write access confirmed for directory: {history_dir}")
        except Exception as e:
            logger.error(f"No write access to directory: {history_dir}")
            logger.error(f"Error details: {str(e)}")
            raise PermissionError(f"No write access to directory: {history_dir}")
            
        # Создаем пустой файл для логов
        log_file = os.path.join(history_dir, "history.log")
        if not os.path.exists(log_file):
            with open(log_file, "w", encoding="utf-8") as f:
                f.write("")
            logger.info(f"Created log file: {log_file}")
        else:
            logger.info(f"Log file already exists: {log_file}")
            
        return True
            
    except Exception as e:
        logger.error(f"Failed to initialize history directory: {str(e)}")
        return False

if __name__ == "__main__":
    success = init_history_directory()
    if success:
        print("History directory initialized successfully")
    else:
        print("Failed to initialize history directory") 