from http import HTTPStatus

from src.interfaces.repository import IRecipeRepository
from src.models.recipe import Recipe, ResponseRecipe
from src.repositories.redis_repository import RedisRepository
from src.exceptions import RecipeErrorNotFound, AuthorizationError


class RecipeService:
    def __init__(
        self, 
        recipe_repository: IRecipeRepository, 
        redis_repository: RedisRepository
    ) -> None:
        self.recipe_repository = recipe_repository
        self.redis_repository = redis_repository

    async def get_recipes(self, offset: int, limit: int):
        cache = await self.redis_repository.get(f"recipes:{offset}&{limit}")
        if cache:
            return cache
        recipes = await self.recipe_repository.get_all(offset, limit)
        if not recipes:
            raise RecipeErrorNotFound(
                message = "recipes not found",
                status_code = HTTPStatus.NOT_FOUND
            )
        await self.redis_repository.insert(
            f"recipes:{offset}&{limit}", recipes
        )
        return recipes

    async def get_recipe(self, id: str):
        cache = await self.redis_repository.get(f"recipe:{id}")
        if cache:
            return cache
        recipe = await self.recipe_repository.get(id)
        if not recipe:
            raise RecipeErrorNotFound(
                message = "recipe not found",
                status_code = HTTPStatus.NOT_FOUND
            )
        await self.redis_repository.insert(f"recipe:{id}", recipe)
        return recipe
            
    async def get_my_recipes(
        self, current_chef_id: str, offset: int, limit: int
    ):
        cache = await self.redis_repository.get(
            f"my_recipes:{current_chef_id}:{offset}&{limit}"
        )
        if cache:
            return cache
        recipes = await self.recipe_repository.get_recipes_from_chef(
            current_chef_id, offset, limit
        )
        if not recipes:
            raise RecipeErrorNotFound(
                message = "recipes not found",
                status_code = HTTPStatus.NOT_FOUND
            )
        await self.redis_repository.insert(
            f"my_recipes:{current_chef_id}:{offset}&{limit}", recipes
        )
        return recipes

    async def add_recipe(self, recipe: Recipe, current_chef_id: str):
        db_recipe = await self.recipe_repository.add(recipe, current_chef_id)
        await self.redis_repository.delete(
            f"my_recipes:{current_chef_id}:*",
            f"recipes:*" 
        )
        return db_recipe

    async def verify_authorization(
        self, current_chef_id: str, recipe_id: str
    ):
        recipe = await self.recipe_repository.get(recipe_id)
        if not recipe:
            raise RecipeErrorNotFound(
                message = "recipe not found",
                status_code = HTTPStatus.NOT_FOUND
            )
        if recipe["chef_id"] != current_chef_id:
            raise AuthorizationError(
                message = "unauthorized request",
                status_code = HTTPStatus.UNAUTHORIZED,
            )

    async def delete_recipe(self, current_chef_id: str, recipe_id: str):
        await self.verify_authorization(current_chef_id, recipe_id)
        await self.recipe_repository.delete(recipe_id)
        await self.redis_repository.delete(
            f"my_recipes:{current_chef_id}:*",
            "recipes:*",
            f"recipe:{recipe_id}"
        )
        return {"message": "Recipe successfully excluded"}

    async def update_recipe(
        self, current_chef_id: str, recipe_id: str, recipe: Recipe
    ):
        await self.verify_authorization(current_chef_id, recipe_id)
        await self.recipe_repository.update(recipe_id, recipe)
        await self.redis_repository.delete(
            f"my_recipes:{current_chef_id}:*",
            "recipes:*",
            f"recipe:{recipe_id}"
        )
        return {"message": "Recipe successfully updated"}
