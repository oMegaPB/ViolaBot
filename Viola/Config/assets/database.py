import os, json

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
            with open(self._path, 'w', encoding='utf-8') as f:
                lines = set(lines)
                for i in lines:
                    f.write(i)
    def add(self, data, check_arg):
        self._clear()
        end_data = ''
        replaced = False
        added = False
        data = json.loads(str(data).replace('\n', '').replace("'", '"'))
        for i in self._getobjects():
            if json.loads(str(i).replace('\n', '').replace("'", '"'))[check_arg] == data[check_arg]:
                end_data += str(data) + '\n'
                replaced = True
            else:
                end_data += str(i) + '\n'
        if not replaced:
            end_data += str(data) + '\n'
            added = True
        with open(self._path, 'w', encoding='utf-8') as f:
            f.write(end_data)
        return {"replaced": str(replaced), "added": str(added)}

    def fetch(self, param, check_value):
        self._clear()
        for i in self._getobjects():
            i = json.loads(str(i).replace('\n', '').replace("'", '"'))
            if str(i[param]) == str(check_value):
                return {'success': 'True', 'value': str(i)}
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
