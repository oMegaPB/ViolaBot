import os, json
from re import L

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
        # txt = DataBase('bdays')
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
