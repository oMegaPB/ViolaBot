import os
from bson.errors import BSONError
from pymongo import MongoClient
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
        username, password = os.environ.get('MONGODB').split(':')
        self.client = MongoClient(f"mongodb+srv://{username}:{password}@cluster0.atwbj6s.mongodb.net/?retryWrites=true&w=majority")
        self.db = self.client[database] if database else self.client['Viola']
        self._operations = 0
    
    @property
    def categories(self) -> List[str]:
        return self.db.list_collection_names()
    
    @property
    def operations(self) -> int:
        return self._operations
    
    @property
    def databases(self):
        return self.client.list_database_names()
    
    async def rows(self, category: str, mode: str = 'str') -> Response:
        """
        |maybecoro|

        Returns all values from specified database category.
        
        """
        self._operations += 1
        if mode == 'str':
            end = ''
            for i in self.db[category].find({}):
                end += str(i) + '\n'
            end = end[:-1]
            if not end == '':
                return Response(status=True, value=end)
            return Response(status=False)
        elif mode == 'list':
            end = []
            for i in self.db[category].find({}):
                end.append(i)
            if len(end) == 0:
                return Response(status=False)
            return Response(status=True, value=end)

    async def add(self, data: Dict[Any, Any], category: str) -> None:
        """
        |maybecoro|

        Adding value into specified category.
        
        """
        self._operations += 1
        try:
            res = await self.fetch(data, category=category)
        except BSONError:
            print('BSON ERROR:', data)
            raise BSONError
        if res.status:
            return
        self.db[category].insert_one(data)

    async def fetch(self, data: Dict[Any, Any], category: str, mode: str = 'one') -> Response:
        """
        |maybecoro|

        Returns values sorted by key from specified database category.
        
        """
        self._operations += 1
        if mode == 'one':
            value = self.db[category].find_one(data)
            if value:
                return Response(status=True, value=value)
            return Response(status=False)
        elif mode == 'all':
            value = []
            for x in self.db[category].find(data):
                value.append(x)
            if len(value) > 0:
                return Response(status=True, value=value)
            return Response(status=False)
    
    async def remove(self, data: Dict[Any, Any], category: str) -> Response:
        """
        |maybecoro|

        Removes item from specified database category.
        
        """
        self._operations += 1
        count = self.db[category].delete_many(data).deleted_count
        if count > 0:
            return Response(status=True, value=count)
        return Response(status=False, value=0)
    
    def drop(self, category: str) -> None:
        """
        |maybecoro|

        Deletes specified category from database.
        
        """
        a = self.db[category]
        a.drop()

# -----------------------------------------------------------------------------------------------------------
# import webbrowser, json2table
# a = MongoDB()
# res = a.fetch({}, mode='all', category='messages').value
# path = os.path.join(os.environ.get('TEMP'), 'tempfile.html')
# with open(path, 'w') as f:
#     for i in res:
#         del i['_id']
#         i['-------'] = '--------------------'
#         html = json2table.convert(i, table_attributes={"style" : "width:100%"})
#         f.write(html)
# webbrowser.open(path)