from .database import SessionLocal, engine
from .models import Base, Role

def init_roles():
    Base.metadata.create_all(bind=engine)
    
    db = SessionLocal()
    
    # Check if roles already exist
    if db.query(Role).count() == 0:
        # Create default roles
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
    init_roles() 