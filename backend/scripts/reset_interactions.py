"""Preview or reset user quest/campaign interactions.

This intentionally preserves content (quests, campaigns, campaign tasks), users,
ordinary task submissions, and admin/unrelated points transactions.
"""

import argparse
import asyncio
from decimal import Decimal

from sqlalchemy import text

from app.core.database import AsyncSessionLocal, engine


REWARD_TYPES = ("Quest_Reward", "Campaign_Reward")


async def scalar(db, sql: str, **params):
    return await db.scalar(text(sql), params)


async def preview(db):
    rows = {
        "quest_completions": await scalar(db, "SELECT count(*) FROM quest_completions"),
        "campaign_task_completions": await scalar(db, "SELECT count(*) FROM campaign_task_completions"),
        "campaign_participations": await scalar(db, "SELECT count(*) FROM campaign_participations"),
        "reward_transactions": await scalar(
            db,
            """SELECT count(*) FROM points_transactions
               WHERE transaction_type::text IN (:quest, :campaign)""",
            quest=REWARD_TYPES[0], campaign=REWARD_TYPES[1],
        ),
        "reward_transaction_points": await scalar(
            db,
            """SELECT COALESCE(sum(amount), 0) FROM points_transactions
               WHERE transaction_type::text IN (:quest, :campaign)""",
            quest=REWARD_TYPES[0], campaign=REWARD_TYPES[1],
        ),
        "reward_ledger_entries": await scalar(
            db,
            """SELECT count(*) FROM pp_ledger_entries
               WHERE transaction_type IN (:quest, :campaign)""",
            quest=REWARD_TYPES[0], campaign=REWARD_TYPES[1],
        ),
        "reward_ledger_points": await scalar(
            db,
            """SELECT COALESCE(sum(amount), 0) FROM pp_ledger_entries
               WHERE transaction_type IN (:quest, :campaign)""",
            quest=REWARD_TYPES[0], campaign=REWARD_TYPES[1],
        ),
    }
    return rows


async def reset(db):
    # Capture the compatibility projection as the one balance adjustment source;
    # each ledger row mirrors one points_transaction and must not be double-counted.
    reward_rows = await db.execute(text("""
        SELECT user_id, COALESCE(sum(amount), 0) AS reward_points
        FROM points_transactions
        WHERE transaction_type::text IN (:quest, :campaign)
        GROUP BY user_id
    """), {"quest": REWARD_TYPES[0], "campaign": REWARD_TYPES[1]})

    user_adjustments = [(row.user_id, Decimal(str(row.reward_points))) for row in reward_rows]

    # Remove interaction state first. Foreign keys on the completion tables make
    # this safe without touching campaign/quest definitions.
    await db.execute(text("DELETE FROM quest_completions"))
    await db.execute(text("DELETE FROM campaign_task_completions"))
    await db.execute(text("DELETE FROM campaign_participations"))

    # Clear campaign accounting produced by participation/completion activity,
    # but preserve campaign definitions, budgets, tasks, and lifecycle settings.
    await db.execute(text("""
        UPDATE campaigns
        SET pp_claimed = 0, pp_reserved = 0, total_participants = 0
    """))

    # Reverse only quest/campaign rewards. GREATEST prevents a stale/spent reward
    # from making a balance invalid; admin and unrelated transactions remain.
    for user_id, reward_points in user_adjustments:
        await db.execute(text("""
            UPDATE users
            SET points = GREATEST(COALESCE(points, 0) - :reward_points, 0),
                available_points = GREATEST(COALESCE(available_points, points, 0) - :reward_points, 0)
            WHERE id = :user_id
        """), {"user_id": user_id, "reward_points": reward_points})

    await db.execute(text("""
        DELETE FROM pp_ledger_entries
        WHERE transaction_type IN (:quest, :campaign)
    """), {"quest": REWARD_TYPES[0], "campaign": REWARD_TYPES[1]})
    await db.execute(text("""
        DELETE FROM points_transactions
        WHERE transaction_type::text IN (:quest, :campaign)
    """), {"quest": REWARD_TYPES[0], "campaign": REWARD_TYPES[1]})


async def main(execute: bool):
    async with AsyncSessionLocal() as db:
        before = await preview(db)
        print("Configured database preview:")
        for key, value in before.items():
            print(f"  {key}: {value}")

        if not execute:
            return

        await reset(db)
        await db.commit()
        after = await preview(db)
        print("Reset committed. Remaining interaction/reward counts:")
        for key, value in after.items():
            print(f"  {key}: {value}")

    await engine.dispose()


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--execute", action="store_true", help="Commit the reset")
    args = parser.parse_args()
    asyncio.run(main(args.execute))
