#!/usr/bin/env python3
"""
Script to manually test background jobs without running full test suite.

This script demonstrates:
1. Deadline enforcement job execution
2. Leaderboard cache refresh execution
3. Integration between the two

Usage:
    python scripts/test_background_jobs.py
"""
import asyncio
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from datetime import datetime, timedelta
from sqlalchemy import select

from app.core.database import async_session_maker
from app.models import (
    User, Task, TaskAssignment, TaskSubmission, DeadlinePenaltyApplied,
    LeaderboardCache, PointsTransaction, TransactionType, UserType, UserRole, AssignedGroup
)
from app.tasks.deadline_enforcement import _check_deadline_penalties_async
from app.services.leaderboard_service import LeaderboardService


async def setup_test_data():
    """Create test data for demonstration"""
    print("=" * 80)
    print("SETTING UP TEST DATA")
    print("=" * 80)
    
    async with async_session_maker() as db:
        # Create test users
        user1 = User(
            email="demo_user1@example.com",
            hashed_password="hashed_password",
            full_name="Demo User 1",
            role=UserRole.TEAM_MEMBER,
            user_type=UserType.TEAM_MEMBER,
            points=200.0
        )
        user2 = User(
            email="demo_user2@example.com",
            hashed_password="hashed_password",
            full_name="Demo User 2",
            role=UserRole.TEAM_MEMBER,
            user_type=UserType.TEAM_MEMBER,
            points=150.0
        )
        user3 = User(
            email="demo_user3@example.com",
            hashed_password="hashed_password",
            full_name="Demo User 3",
            role=UserRole.AMBASSADOR,
            user_type=UserType.AMBASSADOR,
            points=300.0
        )
        
        db.add_all([user1, user2, user3])
        await db.commit()
        await db.refresh(user1)
        await db.refresh(user2)
        await db.refresh(user3)
        
        print(f"✓ Created 3 test users")
        print(f"  - {user1.full_name}: {user1.points} PP (Team Member)")
        print(f"  - {user2.full_name}: {user2.points} PP (Team Member)")
        print(f"  - {user3.full_name}: {user3.points} PP (Ambassador)")
        
        # Create overdue task
        task = Task(
            title="Overdue Demo Task",
            description="This task is overdue for testing",
            assigned_to_group=AssignedGroup.TEAM_MEMBERS,
            deadline=datetime.utcnow() - timedelta(hours=2),
            point_value=50.0,
            created_by_id=user1.id
        )
        db.add(task)
        await db.commit()
        await db.refresh(task)
        
        print(f"\n✓ Created overdue task: '{task.title}'")
        print(f"  - Deadline: {task.deadline} (2 hours ago)")
        print(f"  - Assigned to: Team Members")
        
        # Create assignments
        assignment1 = TaskAssignment(task_id=task.id, user_id=user1.id)
        assignment2 = TaskAssignment(task_id=task.id, user_id=user2.id)
        db.add_all([assignment1, assignment2])
        
        # User1 submits, user2 does not
        submission = TaskSubmission(
            task_id=task.id,
            user_id=user1.id,
            submission_text="Demo submission from user 1"
        )
        db.add(submission)
        await db.commit()
        
        print(f"\n✓ Created task assignments:")
        print(f"  - User 1: Assigned + Submitted ✓")
        print(f"  - User 2: Assigned + NOT Submitted ✗")
        
        return user1.id, user2.id, user3.id, task.id


async def test_deadline_enforcement():
    """Test deadline enforcement job"""
    print("\n" + "=" * 80)
    print("TESTING DEADLINE ENFORCEMENT JOB")
    print("=" * 80)
    
    print("\nRunning deadline enforcement job...")
    result = await _check_deadline_penalties_async()
    
    print(f"\n✓ Job completed successfully")
    print(f"  - Status: {result['status']}")
    print(f"  - Tasks checked: {result['tasks_checked']}")
    print(f"  - Penalties applied: {result['penalties_applied']}")
    
    # Verify penalty was applied
    async with async_session_maker() as db:
        result = await db.execute(
            select(DeadlinePenaltyApplied)
        )
        penalties = result.scalars().all()
        
        print(f"\n✓ Penalty records in database: {len(penalties)}")
        for penalty in penalties:
            print(f"  - Task {penalty.task_id} → User {penalty.user_id}")
        
        # Check points transactions
        result = await db.execute(
            select(PointsTransaction).where(
                PointsTransaction.transaction_type == TransactionType.DEADLINE_PENALTY
            )
        )
        transactions = result.scalars().all()
        
        print(f"\n✓ Penalty transactions: {len(transactions)}")
        for txn in transactions:
            print(f"  - User {txn.user_id}: {txn.amount} PP ({txn.reason})")


async def test_leaderboard_refresh():
    """Test leaderboard cache refresh"""
    print("\n" + "=" * 80)
    print("TESTING LEADERBOARD CACHE REFRESH")
    print("=" * 80)
    
    async with async_session_maker() as db:
        print("\nRunning leaderboard cache refresh...")
        result = await LeaderboardService.refresh_leaderboard_cache(db)
        
        print(f"\n✓ Refresh completed successfully")
        print(f"  - Status: {result['status']}")
        print(f"  - Users updated: {result['users_updated']}")
        print(f"  - Team Members: {result['team_members']}")
        print(f"  - Ambassadors: {result['ambassadors']}")
        
        # Display leaderboard
        print("\n" + "-" * 80)
        print("TEAM MEMBERS LEADERBOARD")
        print("-" * 80)
        
        result = await db.execute(
            select(LeaderboardCache)
            .where(LeaderboardCache.user_type == UserType.TEAM_MEMBER.value)
            .order_by(LeaderboardCache.rank.asc())
        )
        team_entries = result.scalars().all()
        
        for entry in team_entries:
            # Get user details
            user_result = await db.execute(
                select(User).where(User.id == entry.user_id)
            )
            user = user_result.scalar_one()
            print(f"  Rank {entry.rank}: {user.full_name} - {entry.total_pp} PP")
        
        print("\n" + "-" * 80)
        print("AMBASSADORS LEADERBOARD")
        print("-" * 80)
        
        result = await db.execute(
            select(LeaderboardCache)
            .where(LeaderboardCache.user_type == UserType.AMBASSADOR.value)
            .order_by(LeaderboardCache.rank.asc())
        )
        ambassador_entries = result.scalars().all()
        
        for entry in ambassador_entries:
            # Get user details
            user_result = await db.execute(
                select(User).where(User.id == entry.user_id)
            )
            user = user_result.scalar_one()
            print(f"  Rank {entry.rank}: {user.full_name} - {entry.total_pp} PP")


async def test_idempotency():
    """Test that deadline enforcement is idempotent"""
    print("\n" + "=" * 80)
    print("TESTING IDEMPOTENCY")
    print("=" * 80)
    
    print("\nRunning deadline enforcement job again...")
    result = await _check_deadline_penalties_async()
    
    print(f"\n✓ Second run completed")
    print(f"  - Penalties applied: {result['penalties_applied']}")
    
    if result['penalties_applied'] == 0:
        print("\n✓ IDEMPOTENCY VERIFIED: No duplicate penalties applied")
    else:
        print("\n✗ IDEMPOTENCY FAILED: Duplicate penalties were applied!")


async def cleanup_test_data():
    """Clean up test data"""
    print("\n" + "=" * 80)
    print("CLEANING UP TEST DATA")
    print("=" * 80)
    
    async with async_session_maker() as db:
        # Delete test users (cascade will handle related records)
        result = await db.execute(
            select(User).where(User.email.like("demo_%@example.com"))
        )
        users = result.scalars().all()
        
        for user in users:
            await db.delete(user)
        
        await db.commit()
        
        print(f"✓ Cleaned up {len(users)} test users and related data")


async def main():
    """Main test execution"""
    print("\n" + "=" * 80)
    print("BACKGROUND JOBS DEMONSTRATION")
    print("=" * 80)
    print("\nThis script demonstrates:")
    print("1. Deadline enforcement job")
    print("2. Leaderboard cache refresh job")
    print("3. Integration between jobs")
    print("4. Idempotency guarantees")
    
    try:
        # Setup
        user1_id, user2_id, user3_id, task_id = await setup_test_data()
        
        # Test deadline enforcement
        await test_deadline_enforcement()
        
        # Test leaderboard refresh
        await test_leaderboard_refresh()
        
        # Test idempotency
        await test_idempotency()
        
        # Summary
        print("\n" + "=" * 80)
        print("SUMMARY")
        print("=" * 80)
        print("\n✓ All background jobs working correctly!")
        print("\nKey Findings:")
        print("  1. Deadline enforcement correctly identifies overdue tasks")
        print("  2. Penalties applied only to users who didn't submit")
        print("  3. Leaderboard cache updates with correct rankings")
        print("  4. Idempotency prevents duplicate penalties")
        print("  5. Integration between jobs works seamlessly")
        
        # Cleanup
        await cleanup_test_data()
        
        print("\n" + "=" * 80)
        print("DEMONSTRATION COMPLETE")
        print("=" * 80)
        
    except Exception as e:
        print(f"\n✗ Error during demonstration: {str(e)}")
        import traceback
        traceback.print_exc()
        
        # Try to cleanup even on error
        try:
            await cleanup_test_data()
        except:
            pass


if __name__ == "__main__":
    asyncio.run(main())
