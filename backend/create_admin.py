"""Create initial admin user in Supabase."""
import asyncio
from app.database.session import get_db_session
from app.services.auth_service import create_user

async def create_admin():
    """Create admin user."""
    print("Creating admin user...")

    async with get_db_session() as db:
        try:
            admin = await create_user(
                db,
                username="admin",
                email="admin@aimonitoring.local",
                password="admin123",
                full_name="System Administrator",
                is_superuser=True
            )

            if admin:
                await db.commit()
                print(f"✅ Admin user created successfully!")
                print(f"   Username: admin")
                print(f"   Email: {admin.email}")
                print(f"   Password: admin123")
                print(f"\n   ⚠️  Change the password after first login!")
            else:
                print("❌ Admin user already exists or creation failed")

        except Exception as e:
            print(f"❌ Error creating admin: {e}")
            await db.rollback()

if __name__ == "__main__":
    asyncio.run(create_admin())
