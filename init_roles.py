from auth.database import SessionLocal, engine
from auth.models import Base, Role
from auth.init_permissions import init_permissions

def init_roles():
    # Создаем все таблицы
    Base.metadata.create_all(bind=engine)
    
    db = SessionLocal()
    try:
        # Проверяем, существуют ли роли
        if db.query(Role).count() == 0:
            # Создаем роли по умолчанию
            roles = [
                Role(name="admin", description="Administrator with full access"),
                Role(name="user", description="Regular user"),
                Role(name="userplus", description="User with extended privileges")
            ]
            
            db.add_all(roles)
            db.commit()
            print("Роли успешно созданы")
            
            # Инициализируем разрешения для ролей
            init_permissions()
        else:
            print("Роли уже существуют")
    except Exception as e:
        print(f"Произошла ошибка: {str(e)}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    init_roles() 