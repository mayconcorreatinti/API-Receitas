from src.interfaces.repository import IChefRepository
from src.models.chef import Chef, ResponseChef
from src.models.auth import FormData
from src.utils import verify_password
from src.repositories.redis_repository import RedisRepository
from src.exceptions import *


class ChefService:
    def __init__(self, chef_repository: IChefRepository, redis_repository: RedisRepository) -> None:
        self.chef_repository = chef_repository
        self.redis_repository = redis_repository

    async def check_authentication(
        self, form_data: FormData
    ):
        chef = await self.chef_repository.get_by_email(
            email=form_data.username
        )
        if not chef or not verify_password(
            form_data.password, chef["password_hash"]
        ):
            raise AuthenticationError(
                message = "Incorrect username or password!",
                status_code = HTTPStatus.FORBIDDEN
            )

    async def _verify_credentials(self, chef_name: str, email: str):
        conflicting_name = await self.chef_repository.get_by_chef_name(
            chef_name=chef_name
        )
        if conflicting_name:
            raise ConflictingNameError(
                message = "This name already exists!",
                status_code = HTTPStatus.CONFLICT
            )
        conflicting_email = await self.chef_repository.get_by_email(
            email=email
        )
        if conflicting_email:
            raise ConflictingEmailError(
                message = "This email already exists!",
                status_code = HTTPStatus.CONFLICT
            )

    @staticmethod
    def check_authorization(chef_id, authenticated_chef_id):
        if chef_id != authenticated_chef_id:
            raise AuthorizationError(
                message = "unauthorized request",
                status_code = HTTPStatus.UNAUTHORIZED 
            )

    async def get_all_the_chefs(self, offset, limit):
        cache = await self.redis_repository.get(f"chefs:{offset}&{limit}")
        if cache:
            return cache
        chefs = await self.chef_repository.get_all(offset, limit)
        if not chefs:
            raise ChefErrorNotFound(
                message = "Chefs not found!",
                status_code = HTTPStatus.NOT_FOUND
            )
        await self.redis_repository.insert(
            f"chefs:{offset}&{limit}", chefs
        )
        return chefs

    async def get_chef(self, id: str):
        cache = await self.redis_repository.get(f"chef:{id}")
        if cache:
            return cache
        chef = await self.chef_repository.get(id=id)
        if not chef:
            raise ChefErrorNotFound(
                message = "Chefs not found!",
                status_code = HTTPStatus.NOT_FOUND
            )
        await self.redis_repository.insert(f"chef:{id}",chef)
        return chef

    async def add_chef(self, chef: Chef):
        await self._verify_credentials(
            chef_name=chef.chef_name, email=chef.email
        )
        await self.chef_repository.add(chef)
        await self.redis_repository.delete("chefs:*")
        chef = await self.chef_repository.get_by_email(email=chef.email)
        return chef

    async def delete_chef(self, chef_id, current_chef):
        self.check_authorization(chef_id, current_chef["chef_id"])
        await self.chef_repository.delete(current_chef["chef_id"])
        await self.redis_repository.delete(
            f"chef:{current_chef["chef_id"]}", "chefs:*"
        )
        return {"message": "Chef successfully excluded"}

    async def update_chef(
        self, updated_chef: Chef, chef_id, current_chef
    ) -> ResponseChef:
        self.check_authorization(chef_id, current_chef["chef_id"])
        await self._verify_credentials(
            updated_chef.chef_name, updated_chef.email
        )
        await self.chef_repository.update(
            current_chef["chef_id"], updated_chef
        )
        await self.redis_repository.delete(
            f"chef:{current_chef["chef_id"]}","chefs:*"
        )
        updated_chef = await self.chef_repository.get_by_email(
            email=updated_chef.email
        )
        return updated_chef
