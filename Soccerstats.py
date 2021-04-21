import requests
from bs4 import BeautifulSoup
from pprint import pprint

leaguesDict = {
    # 1: 'argentina',
    2: 'austria',
    # 3: 'australia',
    4: 'belgium',
    # 5: 'brazil',
    6: 'germany',
    # 7: 'germany2',
    # 8: 'denmark',
    9: 'england',
    10: 'england2',
    11: 'england3',
    12: 'spain',
    13: 'spain2',
    14: 'finland',
    15: 'france',
    16: 'france2',
    17: 'netherlands',
    18: 'netherlands2',
    19: 'italy',
    20: 'italy2',
    21: 'japan',
    # 22: 'norway',
    # 23: 'poland',
    24: 'portugal',
    25: 'russia',
    26: 'russia2',
    # 27: 'scotland',
    # 28: 'sweden',
    29: 'turkey',
}

# Показываем список лиг
pprint(leaguesDict)
print()

# Вводим номер выбранной лиги (key) и берём соответствующую страну (value) из словаря leaguesDict
league = leaguesDict[int(input('Введите номер лиги из списка выше: '))]
print()

# Список параметров для передачи в requests.get
linkParams = {'league': league, 'pmtype': 'round98'}

# response = requests.get("https://www.soccerstats.com/latest.asp?league=russia")
# Собираем ссылку из параметров linkParams на нужную лигу > прошедший matchday
response = requests.get("https://www.soccerstats.com/results.asp", params=linkParams)
page = response.text
soup = BeautifulSoup(page, 'html.parser')

# Забираем заголовок прошедшего matchday, чтобы получить номер прошедшего тура
# Первый элемент <h2>, непосредственно вложенный в <div>
headings = map(lambda e: e.text, soup.select("div > h2"))
for h in headings:
    # Забираем номер прошедшего тура из заголовка
    previousMatchday = int(h[-2] + h[-1])
    # Высчитываем номер следующего тура (+1 к номеру прошешего тура)
    actualMatchday = previousMatchday + 1

# Обновляем параметр pmtype для перехода на страницу со следующим туром
linkParams['pmtype'] = 'round' + str(actualMatchday)

# Собираем ссылку из обновлённых параметров linkParams на нужную лигу > следующий matchday
response = requests.get("https://www.soccerstats.com/results.asp", params=linkParams)
# response = requests.get("https://www.soccerstats.com/results.asp?league=russia&pmtype=round24")
page = response.text
soup = BeautifulSoup(page, 'html.parser')

# Забираем таблицу с расписанием матчей
# 2-я и 4-я ячейки (<td>) из строк <tr class = "odd"> таблицы, следующей сразу за <h2>
gamesList = list(map(lambda e: e.text, soup.select("div > h2 + table tr.odd td:nth-child(2n+2)")))
for g in gamesList:
    if g == '':
        gamesList.remove(g)

# Создаём из списка с расписанием строку с командами и удаляем ненужные символы, переводим строку в список методом split
gamesString = str(gamesList).replace('\\xa0', '').replace('[', '').replace(']', '').replace("'", '').split(', ')

# Высчитываем количество матчей в туре (кол-во команд делим пополам)
matchesQuantity = int(len(gamesString) / 2)

# Список команд-хозяев
homeTeams = []
# Список команд-гостей
awayTeams = []

for i in range(matchesQuantity * 2):
    if i % 2 == 0:
        # Заполняем список хозяев чётными командами из gamesString
        homeTeams.append(gamesString[i])
    else:
        # Заполняем список гостей нечётными командами из gamesString
        awayTeams.append(gamesString[i])

# Забираем ссылки на все команды из выпадающего списка Teams
teamsDropList = soup.select("div.six table tr td:nth-child(3) div.dropdown a")

# Словарь всех команд и ссылок на их страницы
teamsLinks = {}

for a in teamsDropList:
    # Заполняем словарь: key = команда; value = ссылка
    teamsLinks[a.contents[0]] = a['href']

# Инвертированный словарь teamsLinks: key = ссылка, value = команда
invTeamsLinks = {value: key for key, value in teamsLinks.items()}

# Словарь домашних команд и голов
homeTeamsStats = {}
# Словарь гостевых команд и голов
awayTeamsStats = {}

# Проходим циклом по каждой команде-хозяйке и забираем статистику голов со страницы команды
for t in homeTeams:
    # print(teamsLinks[t])
    # print(invTeamsLinks[teamsLinks[t]])
    # Собираем ссылку на страницу команды из списка хозяев
    response = requests.get("https://www.soccerstats.com/" + teamsLinks[t])
    page = response.text
    soup = BeautifulSoup(page, 'html.parser')

    # Забираем кол-во сыгранных матчей
    gamesQuantity = list(map(lambda e: e.text, soup.select(
        'div.tabbertabdefault td:-soup-contains("Matches played") + td font[color="green"]')))

    # Забираем таблицу Goal times для каждой команды-хозяйки
    goalTimes = list(map(lambda e: e.text, soup.select("div.five div.tabbertab table + table tr:nth-child(1n+16)")))

    for g in goalTimes:
        if g == '':
            goalTimes.remove(g)

    # Создаём из списка с голами строку и удаляем ненужные символы, переводим строку в список методом split
    goalTimesString = str(goalTimes).replace('\\n\\n\\n', ' ').replace('\\n', '').replace("'", "").replace(',', '')\
        .replace('[', '').replace(']', '').replace('GF', '').replace('GA', '').replace(' half', '-half ').split()

    # Создаём список с голами команды-хозяйки и добавляем в список кол-во сыгранных матчей
    homeGoals = [gamesQuantity[0]]

    # Добавляем в список только голы (без текстовых строк)
    for z in goalTimesString:
        if z.isdecimal():
            homeGoals.append(z)

    # Заполняем словарь команд и голов: key = команда; value = список голов
    homeTeamsStats[invTeamsLinks[teamsLinks[t]]] = homeGoals

# Проходим циклом по каждой гостевой команде и забираем статистику голов со страницы команды
for t in awayTeams:
    # print(teamsLinks[t])
    # print(invTeamsLinks[teamsLinks[t]])
    # Собираем ссылку на страницу команды из списка гостей
    response = requests.get("https://www.soccerstats.com/" + teamsLinks[t])
    page = response.text
    soup = BeautifulSoup(page, 'html.parser')

    # Забираем кол-во сыгранных матчей
    gamesQuantity = list(map(lambda e: e.text, soup.select(
        'div.tabbertabdefault td:-soup-contains("Matches played") + td font[color="green"]')))

    # Забираем таблицу Goal times для каждой гостевой команды
    goalTimes = list(map(lambda e: e.text, soup.select("div.five div.tabbertab table + table tr:nth-child(1n+16)")))

    for g in goalTimes:
        if g == '':
            goalTimes.remove(g)

    # Создаём из списка с голами строку и удаляем ненужные символы, переводим строку в список методом split
    goalTimesString = str(goalTimes).replace('\\n\\n\\n', ' ').replace('\\n', '').replace("'", "").replace(',', '')\
        .replace('[', '').replace(']', '').replace('GF', '').replace('GA', '').replace(' half', '-half ').split()

    # Создаём список с голами гостевой команды и добавляем в список кол-во сыгранных матчей
    awayGoals = [gamesQuantity[0]]

    # Добавляем в список только голы (без текстовых строк)
    for z in goalTimesString:
        if z.isdecimal():
            awayGoals.append(z)

    # Заполняем словарь команд и голов: key = команда; value = список голов
    awayTeamsStats[invTeamsLinks[teamsLinks[t]]] = awayGoals

# Список значений словаря домашних команд и голов
hTSKeys = list(homeTeamsStats.keys())
# Список значений словаря гостевых команд и голов
aTSKeys = list(awayTeamsStats.keys())

# Цикл для обхода пар "хозяин - гость", подсчёта среднего кол-ва голов и вывода результатов
for h, a, z, q in zip(homeTeamsStats, awayTeamsStats, range(len(hTSKeys)), range(len(aTSKeys))):
    # Среднее кол-во забитых и пропущенных голов хозяином в домашнем матче в 1-м тайме
    half_1_home = (int(homeTeamsStats[h][5]) + int(homeTeamsStats[h][6])) / int(homeTeamsStats[h][0])
    # Среднее кол-во забитых и пропущенных голов хозяином в домашнем матче во 2-м тайме
    half_2_home = (int(homeTeamsStats[h][7]) + int(homeTeamsStats[h][8])) / int(homeTeamsStats[h][0])

    # Среднее кол-во забитых и пропущенных голов гостем в выездном матче в 1-м тайме
    half_1_away = (int(awayTeamsStats[a][9]) + int(awayTeamsStats[a][10])) / int(awayTeamsStats[a][0])
    # Среднее кол-во забитых и пропущенных голов гостем в выездном матче во 2-м тайме
    half_2_away = (int(awayTeamsStats[a][11]) + int(awayTeamsStats[a][12])) / int(awayTeamsStats[a][0])

    # Тотал голов в 1-м тайме (округляем до сотых)
    half_1_total = round((half_1_home + half_1_away), 2)
    # Тотал голов во 2-м тайме (округляем до сотых)
    half_2_total = round((half_2_home + half_2_away), 2)
    # Тотал голов в матче (округляем до сотых)
    match_total = round((half_1_total + half_2_total), 2)

    print(f'{hTSKeys[z]} - {aTSKeys[q]}.\n'
          f'Тотал голов в 1-м тайме: {half_1_total}\n'
          f'Тотал голов во 2-м тайме: {half_2_total}\n'
          f'Тотал голов в матче: {match_total}\n')
