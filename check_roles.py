from auth.database import SessionLocal
from auth.models import Role

def check_roles():
    db = SessionLocal()
    try:
        roles = db.query(Role).all()
        if roles:
            print("\nСуществующие роли:")
            for role in roles:
                print(f"ID: {role.id}, Name: {role.name}, Description: {role.description}")
        else:
            print("Роли не найдены в базе данных")
    except Exception as e:
        print(f"Произошла ошибка: {str(e)}")
    finally:
        db.close()

if __name__ == "__main__":
    check_roles() 