from auth.database import SessionLocal, engine
from auth.models import Base, Role, User
from auth.init_permissions import init_permissions

def setup_admin(email: str):
    # Создаем все таблицы
    Base.metadata.create_all(bind=engine)
    
    db = SessionLocal()
    try:
        # Проверяем, существуют ли роли
        if db.query(Role).count() == 0:
            print("Создаем роли...")
            # Создаем роли по умолчанию
            roles = [
                Role(name="admin", description="Administrator with full access"),
                Role(name="user", description="Regular user"),
                Role(name="userplus", description="User with extended privileges")
            ]
            
            db.add_all(roles)
            db.commit()
            print("Роли успешно созданы")
            
            # Инициализируем разрешения
            init_permissions()
            print("Разрешения успешно инициализированы")
        else:
            print("Роли уже существуют")
        
        # Находим пользователя
        user = db.query(User).filter(User.email == email).first()
        if not user:
            print(f"Пользователь с email {email} не найден")
            return False

        # Находим роль admin
        admin_role = db.query(Role).filter(Role.name == 'admin').first()
        if not admin_role:
            print("Роль admin не найдена")
            return False

        # Обновляем роль пользователя
        user.role_id = admin_role.id
        db.commit()
        print(f"Роль пользователя {user.email} успешно обновлена на admin")
        return True
        
    except Exception as e:
        print(f"Произошла ошибка: {str(e)}")
        db.rollback()
        return False
    finally:
        db.close()

if __name__ == "__main__":
    email = "xxx@gmail.com"
    if setup_admin(email):
        print("Операция выполнена успешно")
    else:
        print("Не удалось выполнить операцию") 