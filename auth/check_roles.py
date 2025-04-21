from .database import SessionLocal, engine
from .models import Base, Role

def check_roles():
    # Создаем все таблицы
    Base.metadata.create_all(bind=engine)
    
    db = SessionLocal()
    
    # Проверяем существующие роли
    roles = db.query(Role).all()
    print("Existing roles:")
    for role in roles:
        print(f"ID: {role.id}, Name: {role.name}, Description: {role.description}")
    
    # Если ролей нет, создаем их
    if not roles:
        print("Creating default roles...")
        roles = [
            Role(name="admin", description="Administrator with full access"),
            Role(name="user", description="Regular user"),
            Role(name="userplus", description="User with extended privileges")
        ]
        db.add_all(roles)
        db.commit()
        print("Default roles created successfully")
    
    db.close()

if __name__ == "__main__":
    check_roles() 