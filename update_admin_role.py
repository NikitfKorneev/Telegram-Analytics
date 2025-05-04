from auth.database import SessionLocal
from auth.models import User, Role

def update_user_to_admin():
    db = SessionLocal()
    try:
        # Находим пользователя
        user = db.query(User).filter(User.email == 'admin@gmail.com').first()
        if not user:
            print("Пользователь с email admin@gmail.com не найден")
            return

        # Находим роль admin
        admin_role = db.query(Role).filter(Role.name == 'admin').first()
        if not admin_role:
            print("Роль admin не найдена")
            return

        # Обновляем роль пользователя
        user.role_id = admin_role.id
        db.commit()
        print(f"Роль пользователя {user.email} успешно обновлена на admin")
        
    except Exception as e:
        print(f"Произошла ошибка: {str(e)}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    update_user_to_admin() 