from auth.database import SessionLocal
from auth.models import Role

def check_admin_permissions():
    db = SessionLocal()
    try:
        # Находим роль admin
        admin_role = db.query(Role).filter(Role.name == 'admin').first()
        if not admin_role:
            print("Роль admin не найдена")
            return

        print(f"\nИнформация о роли admin:")
        print(f"ID: {admin_role.id}")
        print(f"Name: {admin_role.name}")
        print(f"Description: {admin_role.description}")
        
        print("\nРазрешения роли admin:")
        for permission in admin_role.permissions:
            print(f"- {permission.name}: {permission.description}")
            
    except Exception as e:
        print(f"Произошла ошибка: {str(e)}")
    finally:
        db.close()

if __name__ == "__main__":
    check_admin_permissions() 