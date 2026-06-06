"""Seed initial data: default tenant, admin user, sample channels, mock AI provider."""
import asyncio
import uuid
import sys
from pathlib import Path

# 让 seed.py 可以独立跑
sys.path.insert(0, str(Path(__file__).parent))

from sqlalchemy import select
from database import AsyncSessionLocal, init_db
from models import User, Channel, Tenant, AIProviderConfig
from auth import hash_password
from config import settings


async def main():
    print("[seed] starting...")
    await init_db()

    async with AsyncSessionLocal() as db:
        # 1. 默认租户
        result = await db.execute(
            select(Tenant).where(Tenant.id == uuid.UUID("00000000-0000-0000-0000-000000000001"))
        )
        tenant = result.scalar_one_or_none()
        if tenant is None:
            tenant = Tenant(
                id=uuid.UUID("00000000-0000-0000-0000-000000000001"),
                slug="default",
                name="Default Community",
            )
            db.add(tenant)
            print("[seed] created default tenant")
        await db.flush()

        # 2. 初始 admin
        result = await db.execute(select(User).where(User.email == settings.INITIAL_ADMIN_EMAIL))
        admin = result.scalar_one_or_none()
        if admin is None:
            admin = User(
                tenant_id=tenant.id,
                email=settings.INITIAL_ADMIN_EMAIL,
                username=settings.INITIAL_ADMIN_USERNAME,
                password_hash=hash_password(settings.INITIAL_ADMIN_PASSWORD),
                display_name="Admin",
                role="admin",
                status="active",
                email_verified=True,
            )
            db.add(admin)
            print(f"[seed] created admin user: {settings.INITIAL_ADMIN_EMAIL} / {settings.INITIAL_ADMIN_PASSWORD}")
        else:
            print(f"[seed] admin user already exists: {settings.INITIAL_ADMIN_EMAIL}")
        await db.flush()

        # 3. 示例频道
        sample_channels = [
            ("announcements", "公告", "官方公告和发布说明", "public"),
            ("general", "随便聊聊", "灌水、闲聊、问问题", "public"),
            ("dev", "开发", "代码、bug、想法", "public"),
            ("showcase", "作品", "展示你做的东西", "public"),
        ]

        for slug, name, desc, vis in sample_channels:
            result = await db.execute(select(Channel).where(Channel.slug == slug))
            if result.scalar_one_or_none() is None:
                ch = Channel(
                    tenant_id=tenant.id,
                    slug=slug,
                    name=name,
                    description=desc,
                    visibility=vis,
                    created_by=admin.id,
                )
                db.add(ch)
                print(f"[seed] created channel: #{slug}")

        # 4. 默认 Mock AI Provider（让 demo 0 配置就能用）
        # seed 默认创建一个 mock provider 并设为 default；
        # 用户随时可以在 /admin/ai 添加真实 Provider 并切换。
        result = await db.execute(select(AIProviderConfig).where(AIProviderConfig.provider_type == "mock"))
        existing_mock = result.scalar_one_or_none()
        if existing_mock is None:
            mock_provider = AIProviderConfig(
                tenant_id=tenant.id,
                name="Mock AI (本地假数据)",
                provider_type="mock",
                api_key="not-required",  # mock 不需要真 key
                base_url="local://mock",
                model="mock-summarizer-v1",
                is_active=True,
                is_default=True,
                supports_chat=True,
                supports_summarize=True,
                supports_embed=False,  # v0.1 mock 不实现 embed
            )
            db.add(mock_provider)
            print("[seed] created default Mock AI provider (no API key needed)")
        else:
            print("[seed] Mock AI provider already exists")

        await db.commit()
        print("[seed] done")
        print()
        print("=" * 50)
        print("OpenCord v0.1 seed complete.")
        print()
        print(f"  Admin URL    : http://localhost:3000")
        print(f"  Admin email  : {settings.INITIAL_ADMIN_EMAIL}")
        print(f"  Admin pass   : {settings.INITIAL_ADMIN_PASSWORD}")
        print()
        print("  Next steps:")
        print("  1. Visit http://localhost:3000")
        print("  2. Login as admin")
        print("  3. Go to any channel and create a post")
        print("  4. Visit the post and trigger AI summary (admin only in v0.1)")
        print("  5. Add a real AI Provider at /admin/ai when ready")
        print("=" * 50)


if __name__ == "__main__":
    asyncio.run(main())
