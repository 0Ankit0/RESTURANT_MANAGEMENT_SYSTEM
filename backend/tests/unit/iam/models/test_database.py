import pytest
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from src.apps.iam.models.user import User, UserProfile
from tests.factories import UserFactory, UserProfileFactory


class TestUserDatabase:
    """Test User model database operations."""
    
    @pytest.mark.asyncio
    async def test_create_user(self, db_session: AsyncSession):
        """Test creating a user in the database."""
        user = UserFactory.build(username="dbuser", email="db@example.com")
        db_session.add(user)
        await db_session.commit()
        await db_session.refresh(user)
        
        assert user.id is not None
        assert user.username == "dbuser"
        assert user.email == "db@example.com"
    
    @pytest.mark.asyncio
    async def test_query_user(self, db_session: AsyncSession):
        """Test querying a user from the database."""
        user = UserFactory.build(username="queryuser")
        db_session.add(user)
        await db_session.commit()
        
        result = await db_session.execute(
            select(User).where(User.username == "queryuser")
        )
        queried_user = result.scalars().first()
        
        assert queried_user is not None
        assert queried_user.username == "queryuser"
    
    @pytest.mark.asyncio
    async def test_update_user(self, db_session: AsyncSession):
        """Test updating a user in the database."""
        user = UserFactory.build(is_active=True)
        db_session.add(user)
        await db_session.commit()
        await db_session.refresh(user)
        
        user.is_active = False
        await db_session.commit()
        await db_session.refresh(user)
        
        assert user.is_active is False
    
    @pytest.mark.asyncio
    async def test_user_with_profile(self, db_session: AsyncSession):
        """Test creating user with profile relationship."""
        user = UserFactory.build(username="profileuser")
        profile = UserProfileFactory.build(user=user)
        
        db_session.add(user)
        db_session.add(profile)
        await db_session.commit()
        await db_session.refresh(user)
        
        assert user.id is not None
        result = await db_session.execute(
            select(UserProfile).where(UserProfile.user_id == user.id)
        )
        user_profile = result.scalars().first()
        assert user_profile is not None
        assert user_profile.user_id == user.id
    
    @pytest.mark.asyncio
    async def test_delete_user(self, db_session: AsyncSession):
        """Test deleting a user from the database."""
        user = UserFactory.build(username="deleteuser")
        db_session.add(user)
        await db_session.commit()
        await db_session.refresh(user)
        user_id = user.id
        
        await db_session.delete(user)
        await db_session.commit()
        
        result = await db_session.execute(
            select(User).where(User.id == user_id)
        )
        deleted_user = result.scalars().first()
        assert deleted_user is None


class TestUserConstraints:
    """Test database constraints on User model."""
    
    @pytest.mark.asyncio
    async def test_unique_username(self, db_session: AsyncSession):
        """Test username uniqueness constraint."""
        user1 = UserFactory.build(username="uniqueuser", email="user1@example.com")
        db_session.add(user1)
        await db_session.commit()
        
        user2 = UserFactory.build(username="uniqueuser", email="user2@example.com")
        db_session.add(user2)
        
        with pytest.raises(Exception):
            await db_session.commit()
    
    @pytest.mark.asyncio
    async def test_unique_email(self, db_session: AsyncSession):
        """Test email uniqueness constraint."""
        user1 = UserFactory.build(username="user1", email="same@example.com")
        db_session.add(user1)
        await db_session.commit()
        
        user2 = UserFactory.build(username="user2", email="same@example.com")
        db_session.add(user2)
        
        with pytest.raises(Exception):
            await db_session.commit()
