from auth.database import SessionLocal, engine
from auth.models import Base, Role, Permission
from auth.init_permissions import init_permissions

def reinit_permissions():
    # Создаем все таблицы
    Base.metadata.create_all(bind=engine)
    
    db = SessionLocal()
    try:
        # Удаляем все существующие разрешения
        db.query(Permission).delete()
        db.commit()
        print("Существующие разрешения удалены")
        
        # Инициализируем разрешения заново
        init_permissions()
        print("Разрешения успешно переинициализированы")
        
    except Exception as e:
        print(f"Произошла ошибка: {str(e)}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    reinit_permissions() 