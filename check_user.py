from auth.database import SessionLocal
from auth.models import User

def check_user(email: str):
    db = SessionLocal()
    try:
        user = db.query(User).filter(User.email == email).first()
        if user:
            print(f"\nИнформация о пользователе:")
            print(f"Email: {user.email}")
            print(f"Username: {user.username}")
            print(f"Role ID: {user.role_id}")
            if user.role:
                print(f"Role name: {user.role.name}")
        else:
            print(f"Пользователь с email {email} не найден")
    except Exception as e:
        print(f"Произошла ошибка: {str(e)}")
    finally:
        db.close()

if __name__ == "__main__":
    check_user("yyy@gmail.com") 