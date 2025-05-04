from auth.database import SessionLocal
from auth.models import Role

def init_roles():
    db = SessionLocal()
    try:
        # Проверяем существующие роли
        existing_roles = db.query(Role).all()
        if existing_roles:
            print("Роли уже существуют:")
            for role in existing_roles:
                print(f"ID: {role.id}, Name: {role.name}, Description: {role.description}")
            return

        # Создаем роли
        roles = [
            Role(name="admin", description="Administrator with full access"),
            Role(name="user", description="Regular user"),
            Role(name="userplus", description="User with extended privileges")
        ]
        
        for role in roles:
            db.add(role)
        db.commit()
        print("Роли успешно созданы:")
        for role in roles:
            print(f"ID: {role.id}, Name: {role.name}, Description: {role.description}")
            
    except Exception as e:
        print(f"Произошла ошибка: {str(e)}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    init_roles() 