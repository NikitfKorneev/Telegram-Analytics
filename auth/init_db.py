from .database import engine, Base
from .models import Role, User
from .database import SessionLocal

def init_db():
    # Создаем все таблицы
    Base.metadata.create_all(bind=engine)
    
    db = SessionLocal()
    
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
        print("Default roles created successfully")
    else:
        print("Roles already exist")
    
    db.close()

if __name__ == "__main__":
    init_db() 