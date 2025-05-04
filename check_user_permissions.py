from auth.database import SessionLocal
from auth.models import User, Role

def check_user_permissions():
    db = SessionLocal()
    try:
        # Находим пользователя
        user = db.query(User).filter(User.email == 'admin@gmail.com').first()
        if not user:
            print("Пользователь с email admin@gmail.com не найден")
            return

        # Проверяем роль и разрешения
        print(f"\nИнформация о пользователе:")
        print(f"Email: {user.email}")
        print(f"Username: {user.username}")
        print(f"Role ID: {user.role_id}")
        
        if user.role:
            print(f"Role name: {user.role.name}")
            print("\nРазрешения пользователя:")
            for permission in user.role.permissions:
                print(f"- {permission.name}: {permission.description}")
        else:
            print("У пользователя не назначена роль!")
            
    except Exception as e:
        print(f"Произошла ошибка: {str(e)}")
    finally:
        db.close()

if __name__ == "__main__":
    check_user_permissions() 