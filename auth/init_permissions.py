from .database import SessionLocal, engine
from .models import Base, Role, Permission

def init_permissions():
    Base.metadata.create_all(bind=engine)
    
    db = SessionLocal()
    
    # Создаем разрешения
    permissions = [
        # Общие разрешения
        Permission(name="view_profile", description="Can view own profile"),
        Permission(name="edit_profile", description="Can edit own profile"),
        
        # Разрешения для файлов
        Permission(name="create_file", description="Can create files"),
        Permission(name="view_file", description="Can view files"),
        Permission(name="edit_file", description="Can edit files"),
        Permission(name="delete_file", description="Can delete files"),
        Permission(name="share_file", description="Can share files with others"),
        
        # Разрешения для аналитики
        Permission(name="view_analytics", description="Can view basic analytics"),
        Permission(name="view_advanced_analytics", description="Can view advanced analytics"),
        
        # Административные разрешения
        Permission(name="manage_users", description="Can manage users"),
        Permission(name="manage_roles", description="Can manage roles"),
        Permission(name="view_all_files", description="Can view all files"),
        Permission(name="manage_system", description="Can manage system settings")
    ]
    
    # Добавляем разрешения в базу данных
    for permission in permissions:
        if not db.query(Permission).filter(Permission.name == permission.name).first():
            db.add(permission)
    db.commit()
    
    # Получаем роли
    admin_role = db.query(Role).filter(Role.name == "admin").first()
    user_role = db.query(Role).filter(Role.name == "user").first()
    userplus_role = db.query(Role).filter(Role.name == "userplus").first()
    
    # Назначаем разрешения для роли admin
    if admin_role:
        admin_permissions = db.query(Permission).all()  # Все разрешения
        admin_role.permissions = admin_permissions
    
    # Назначаем разрешения для роли user
    if user_role:
        user_permissions = db.query(Permission).filter(
            Permission.name.in_([
                "view_profile",
                "edit_profile",
                "create_file",
                "view_file",
                "edit_file",
                "delete_file",
                "view_analytics"
            ])
        ).all()
        user_role.permissions = user_permissions
    
    # Назначаем разрешения для роли userplus
    if userplus_role:
        userplus_permissions = db.query(Permission).filter(
            Permission.name.in_([
                "view_profile",
                "edit_profile",
                "create_file",
                "view_file",
                "edit_file",
                "delete_file",
                "share_file",
                "view_analytics",
                "view_advanced_analytics"
            ])
        ).all()
        userplus_role.permissions = userplus_permissions
    
    db.commit()
    print("Permissions initialized successfully")
    
    db.close()

if __name__ == "__main__":
    init_permissions() 