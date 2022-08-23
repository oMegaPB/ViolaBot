from motor.motor_asyncio import AsyncIOMotorClient
import os, asyncio
from bson.errors import BSONError
from typing import Optional, Any, Dict, List
# -----------------------------------------------------------------------------------------------------------
class Response:
    """
    Base class for Database response.
    \n`Parameters`:\n
    `status`: represents the respose status. (bool)\n
    `value`: if status True, value of query. (Optional[Any])
    
    """
    def __init__(self, status: bool, value: Optional[Any] = None) -> None:
        self._status = status
        self._value = value if value is not None else None
    
    def __str__(self) -> str:
        return f'<Response status: {self._status}, value: {self._value}>'
    
    @property
    def status(self) -> bool:
        return self._status
    
    @property
    def value(self) -> Any:
        return self._value
# -----------------------------------------------------------------------------------------------------------
class MongoDB:
    def __init__(self, database: Optional[str] = None) -> None:
        self.loop = asyncio.new_event_loop()
        username, password = os.environ.get('MONGODB').split(':')
        self.client = AsyncIOMotorClient(f"mongodb+srv://{username}:{password}@cluster0.atwbj6s.mongodb.net/?retryWrites=true&w=majority")
        self.db = self.client[database] if database else self.client['Viola']
        self._operations = 0
    
    @property
    def categories(self) -> List[str]:
        end = []
        async def _wrapper():
            for i in await self.db.list_collection_names():
                end.append(i)
        self.loop.run_until_complete(_wrapper())
        return end
    
    @property
    def operations(self) -> int:
        return self._operations
    
    @property
    def databases(self) -> List[str]:
        end = []
        async def _wrapper():
            for i in await self.client.list_database_names():
                end.append(i)
        self.loop.run_until_complete(_wrapper())
        return end

    async def add(self, data: Dict[Any, Any], category: str) -> None:
        """
        |coro|

        Adding value into specified category.
        
        """
        self._operations += 1
        try:
            res = await self.fetch(data, category=category)
        except BSONError:
            print('BSON ERROR:', data)
            return
        if res.status:
            return
        await self.db[category].insert_one(data)

    async def fetch(self, data: Dict[Any, Any], category: str, mode: str = 'one') -> Response:
        """
        |coro|

        Returns values sorted by key from specified database category.
        
        """
        self._operations += 1
        if mode == 'one':
            value = await self.db[category].find_one(data)
            if value:
                return Response(status=True, value=value)
            return Response(status=False)
        elif mode == 'all':
            value = []
            async for x in self.db[category].find(data):
                value.append(x)
            if len(value) > 0:
                return Response(status=True, value=value)
            return Response(status=False)
    
    async def remove(self, data: Dict[Any, Any], category: str) -> Response:
        """
        |coro|

        Removes item from specified database category.
        
        """
        self._operations += 1
        count = await self.db[category].delete_many(data)
        count = count.deleted_count
        if count > 0:
            return Response(status=True, value=count)
        return Response(status=False, value=0)
    
    async def drop(self, category: str) -> None:
        """
        |coro|

        Deletes specified category from database.
        
        """
        await self.db[category].drop()
# -----------------------------------------------------------------------------------------------------------