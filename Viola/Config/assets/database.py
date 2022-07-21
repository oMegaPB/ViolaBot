import os, json
from pymongo import MongoClient
from typing import Optional
# -----------------------------------------------------------------------------------------------------------
class DataBase:
    def __init__(self, name: str):
        self._name = name
        self._path = os.path.join(os.path.dirname(os.path.realpath(__file__)) + '/', f'{self._name}.txt')
        if not os.path.exists(self._path):
            raise RuntimeError(f'Cannot find {self._name}')

    @property
    def values(self):
        with open(self._path, 'r') as file:
            return len(file.readlines())
    @property
    def name(self):
        return self._name + '.txt'
    @property
    def path(self):
        return self._path

    def _getobjects(self, *obj):
        with open(self._path, 'r', encoding='utf-8') as file:
            for i in file.readlines():
                i = json.loads(i.replace('\n', '').replace("'", '"'))
                try:
                    if not obj:
                        yield i
                    else:
                        yield i[obj[0]]
                except KeyError:
                    continue
    def _getobjectsjson(self, *obj):
        with open(self._path, 'r', encoding='utf-8') as file:
            for i in file.readlines():
                i = json.loads(i.replace('\n', '').replace("'", '"'))
                try:
                    if not obj:
                        yield json.loads(str(i).replace('\n', '').replace("'", '"'))
                    else:
                        yield i[obj[0]]
                except KeyError:
                    continue
    def _clear(self):
        with open(self._path, 'r', encoding='utf-8') as file:
            lines = file.readlines()
            ln = len(lines)
            with open(self._path, 'w', encoding='utf-8') as f:
                lines = set(lines)
                lin = len(lines)
                for i in lines:
                    f.write(i)
        if ln > lin:
            return 1
        return 0
    def add(self, data, *check_arg):
        end_data = ''
        replaced = False
        added = False
        data = json.loads(str(data).replace('\n', '').replace("'", '"'))
        if check_arg:
            for i in self._getobjects():
                if json.loads(str(i).replace('\n', '').replace("'", '"'))[check_arg[0]] == data[check_arg[0]]:
                    end_data += str(data) + '\n'
                    replaced = True
                else:
                    end_data += str(i) + '\n'
        if not replaced:
            if not check_arg:
                for i in self._getobjects():
                    end_data += str(i) + '\n'
            end_data += str(data) + '\n'
            added = True
        with open(self._path, 'w', encoding='utf-8') as f:
            f.write(end_data)
        res = self._clear()
        return {"replaced": str(replaced), "added": str(added), 'cleared': res}

    def fetch(self, param, check_value):
        self._clear()
        for i in self._getobjects():
            i = json.loads(str(i).replace('\n', '').replace("'", '"'))
            if str(i[param]) == str(check_value):
                return {'success': 'True', 'value': str(i)}
        return {'success': 'False'}

    def fetchl(self, param, check_value):
        self._clear()
        lst = []
        appended = False
        for i in self._getobjects():
            i = json.loads(str(i).replace('\n', '').replace("'", '"'))
            if str(i[param]) == str(check_value):
                lst.append(str(i))
                appended = True
        if appended:
            return {'success': 'True', 'value': lst}
        return {'success': 'False'}
    
    def remove(self, key, value):
        # txt = DataBase('dbays')
        # txt.remove('author', 'Ded#8089')
        end_value = ''
        done = False
        for i in self._getobjectsjson():
            if not i[key] == value:
                end_value += str(i) + '\n'
            else: 
                done = True
        with open(self._path, 'w', encoding='utf-8') as file:
            file.write(end_value)
        return {'done': f'{done}'}
# -----------------------------------------------------------------------------------------------------------
class MongoDB:
    def __init__(self, category: Optional[str] = None, database: Optional[str] = None) -> None:
        self.client = MongoClient(f"mongodb+srv://griefer228666:SDpWx8YgJ8a0sfRS@cluster0.atwbj6s.mongodb.net/?retryWrites=true&w=majority")
        self.db = self.client[database] if database else self.client['Viola']
        self.category = category if category else self.db['nocategory']

    @property
    def categories(self):
        return self.db.list_collection_names()
    
    def rows(self, category: str) -> str:
        end = ''
        for i in self.db[category].find({}):
            end += str(i) + '\n'
        return end

    def clear(self, data: dict, category: str) -> None:
        a = self.remove(data, category=category)
        self.db[category].insert_one(data)
        if a['done'] == 'True':
            return 1
        return 0

    def add(self, data: dict, check: dict = None, category: str = 'nocategory') -> dict:
        replaced = False
        added = False
        if check is None:
            res = self.clear(data, category=category)
            added = True
            return {"replaced": str(replaced), "added": str(added), 'cleared': res}
        args = self.fetch(check, category=category)
        if args is not None:
            self.db[category].find_one_and_replace(args, data)
            replaced = True
            res = self.clear(data, category=category)
            return {"replaced": str(replaced), "added": str(added), 'cleared': res}
        args = self.fetch(data, category=category)
        if data != args:
            self.db[category].insert_one(data)
            added = True
        res = self.clear(data, category=category)
        return {"replaced": str(replaced), "added": str(added), 'cleared': res}
        

    def fetch(self, data: dict, mode: str = 'one', category: str = 'nocategory') -> dict:
        if mode == 'one':
            value = self.db[category].find_one(data)
            if value:
                return {'success': 'True', 'value': value}
            return {'success': 'False'}
        elif mode == 'all':
            value = []
            for x in self.db[category].find(data):
                value.append(x)
            if len(value) > 0:
                return {'success': 'True', 'value': value}
            return {'success': 'False'}
    
    def remove(self, data: dict, category: str) -> int:
        count = self.db[category].delete_many(data).deleted_count
        if count > 0:
            return {'done': f'{True}'}
        return {'done': f'{False}'}
# -----------------------------------------------------------------------------------------------------------