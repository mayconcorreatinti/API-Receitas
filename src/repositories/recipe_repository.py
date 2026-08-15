from datetime import datetime
from typing import List
from uuid import uuid4

from src.interfaces.connection_db import IDBConnection
from src.interfaces.repository import IRecipeRepository
from src.models.recipe import Recipe, ResponseRecipe


class RecipeRepository(IRecipeRepository):
    def __init__(self, connection: IDBConnection, collection_name: str = "Recipe") -> None:
        self.connection = connection
        self.collection_name = collection_name

    async def get_all(self, offset: int, limit: int) -> List[ResponseRecipe]:
        async with self.connection:
            response = await self.connection.execute(
                {
                    "find": self.collection_name
                },
                {
                    "filter": {}, 
                    "skip": offset, 
                    "limit": limit
                }
            )
            return response["cursor"]["firstBatch"]

    async def get(self, id: str):
        async with self.connection:
            response = await self.connection.execute(
                {
                    "find": self.collection_name
                },
                {
                    "filter": {
                        "recipe_id": id
                    }, 
                    "limit": 1
                }
            )
            cursor = response.get("cursor", {}).get("firstBatch", [])
            return cursor[0] if cursor else None

    async def get_recipes_from_chef(
        self, current_chef_id: str, offset: int, limit: int
    ):
        async with self.connection:
            response = await self.connection.execute(
                {
                    "find": self.collection_name
                },
                {
                    "filter": {
                        "chef_id": current_chef_id
                    }, 
                    "skip": offset, 
                    "limit": limit
                }
            )
            return response["cursor"]["firstBatch"]

    async def add(self, recipe: Recipe, current_chef_id: str):
        async with self.connection:
            unique_id = uuid4()
            db_recipe = {
                "recipe_id": str(unique_id),
                "chef_id": current_chef_id,
                **recipe.model_dump(),
                "posted_at": datetime.now(),
                "updated_at": datetime.now(),
            }
            await self.connection.execute(
                {
                    "insert": self.collection_name
                },
                {
                    "documents": [
                        db_recipe
                    ]
                }
            )
            return db_recipe

    async def delete(self, recipe_id: str):
        async with self.connection:
            await self.connection.execute(
                {
                    "delete": self.collection_name
                },
                {
                    "deletes": [
                        {
                            "q": {
                                "recipe_id": recipe_id
                            }, 
                            "limit": 1
                        }
                    ]
                }
            )

    async def update(self, recipe_id: str, recipe: Recipe):
        async with self.connection:
            await self.connection.execute(
                {
                    "update": self.collection_name
                },
                {
                    "updates": [
                        {
                            "q": {
                                "recipe_id": recipe_id
                            },
                            "u": {
                                "$set": recipe.model_dump()
                            },
                            "upsert": False,
                        }
                    ]
                },
            )
