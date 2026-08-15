from datetime import datetime
from typing import List
from uuid import uuid4

from src.interfaces.connection_db import IDBConnection
from src.interfaces.repository import IChefRepository
from src.models.chef import Chef
from src.utils import hash


class ChefRepository(IChefRepository):
    def __init__(self, connection: IDBConnection) -> None:
        self.connection = connection

    async def get_all(self, offset: int, limit: int) -> List[Chef]:
        chefs = await self.connection.execute(
            """
            SELECT chef_id,
                chef_name,
                email,
                create_at,
                updated_at
            FROM chef
            LIMIT %s
            OFFSET %s;
        """,
            (limit, offset),
        )
        return chefs

    async def get(self, id: str) -> Chef:
        chef_list = await self.connection.execute(
            """
            SELECT chef_id,
                chef_name,
                email,
                password_hash,
                create_at,
                updated_at
            FROM chef
            WHERE chef_id = %s;
        """,
            (id,),
        )
        for chef in chef_list:
            return chef

    async def get_by_email(self, email: str) -> Chef:
        chef_list = await self.connection.execute(
            """
            SELECT chef_id,
                chef_name,
                email,
                password_hash,
                create_at,
                updated_at
            FROM chef
            WHERE email = %s;
        """,
            (email,),
        )
        for chef in chef_list:
            return chef

    async def get_by_chef_name(self, chef_name: str) -> Chef:
        chef_list = await self.connection.execute(
            """
            SELECT chef_id,
                chef_name,
                email,
                password_hash,
                create_at,
                updated_at
            FROM chef
            WHERE chef_name = %s;
        """,
            (chef_name,),
        )
        for chef in chef_list:
            return chef

    async def add(self, data: Chef) -> None:
        await self.connection.execute(
            """
            INSERT INTO chef(
                chef_id,
                chef_name,
                email,
                password_hash
            )
            VALUES (%s,%s,%s,%s);
        """,
            (str(uuid4()), data.chef_name, data.email, hash(data.password)),
        )

    async def delete(self, id: str) -> None:
        await self.connection.execute(
            """
            DELETE FROM chef WHERE chef_id = %s;
        """,
            (id,),
        )

    async def update(self, id: str, data: Chef) -> None:
        await self.connection.execute(
            """
            UPDATE chef SET
                chef_name = %s,
                email = %s,
                updated_at = %s,
                password_hash = %s
            WHERE chef_id = %s;
        """,
            (
                data.chef_name,
                data.email,
                datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                hash(data.password),
                id,
            ),
        )
