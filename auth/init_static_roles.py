from .database import SessionLocal, engine
from .models import Base, Role

def init_static_roles():
    # Создаем все таблицы
    Base.metadata.create_all(bind=engine)
    
    db = SessionLocal()
    
    # Удаляем все существующие роли
    db.query(Role).delete()
    db.commit()
    
    # Создаем статические роли
    roles = [
        Role(name="admin", description="Administrator with full access"),
        Role(name="user", description="Regular user"),
        Role(name="userplus", description="User with extended privileges")
    ]
    
    db.add_all(roles)
    db.commit()
    print("Static roles created successfully")
    
    # Выводим список созданных ролей
    print("\nCreated roles:")
    for role in db.query(Role).all():
        print(f"ID: {role.id}, Name: {role.name}, Description: {role.description}")
    
    db.close()

if __name__ == "__main__":
    init_static_roles() 