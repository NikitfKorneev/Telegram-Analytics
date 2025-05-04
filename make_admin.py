from auth.database import SessionLocal
from auth.models import User, Role

def make_user_admin(email: str):
    db = SessionLocal()
    try:
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
    email = "yyy@gmail.com"
    if make_user_admin(email):
        print("Операция выполнена успешно")
    else:
        print("Не удалось выполнить операцию") 