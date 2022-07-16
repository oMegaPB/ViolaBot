import requests, threading
from Config.settings import apikey

class Gtop:
    def __init__(self, name):
        self.name = name
        self.all = ['-', '-', '-', '-', '-', '-', '-', '-', '-', '-']
    def GetNamesThread(self, uuid, pos):
        self.all[pos] = (requests.get(f'https://api.mojang.com/user/profiles/{uuid}/names').json()[-1]['name'])
    def GetGexp(self, day):
        self.response = requests.get(f'https://api.hypixel.net/guild?key={apikey}&name={self.name}').json()
        if str(self.response['guild']) != 'None':
            top10 = []
            for i in range(len(self.response['guild']['members'])):
                uuid = self.response['guild']['members'][i]['uuid']
                gexp = list(self.response['guild']['members'][i]['expHistory'].values())[day-1]
                if int(gexp) != 0:
                    top10.append({'uuid': uuid, 'gexp': int(gexp)})
            if len(top10) == 0:
                return 'None'
            top10 = sorted(top10, key = lambda d: d['gexp'])
            count = -1
            topers = []
            if len(top10) < 10:
                mems = len(top10)
            else:
                mems = 10
            for i in range(mems):
                topers.append(top10[count])
                count -= 1
            final = []
            pos = 0
            for i in topers:
                uuid = i['uuid']
                threading.Thread(target=self.GetNamesThread, args=(uuid, pos)).start()
                pos += 1
            while (10 - int(self.all.count("-"))) != len(topers):
                pass
            count = 0
            for i in range(len(topers)):
                final.append({'name': self.all[i], 'gexp': topers[count]['gexp']})
                count +=1
            return [final, self.response['guild']['name'], list(self.response['guild']['members'][0]['expHistory'].keys())[day-1], len(self.response['guild']['members'])]