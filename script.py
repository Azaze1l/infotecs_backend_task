from aiohttp import web
import json
from math import ceil

# Данные из файла RU.txt сохраняются в список
file = open('RU.txt', 'r', encoding='utf-8')
cities_list = []
for line in file:
    cities_list.append(line.split('\t'))


def make_a_city_dict(city):
    """
    Вспомогательная функция; создает словарь, содержащий свойства города.
    """
    city_dict = {'geonameid': city[0], 'name': city[1],
                 'asciiname': city[2], 'alternatenames': city[3],
                 'latitude': city[4], 'longtitude': city[5],
                 'feature_class': city[6], 'feature_code': city[7],
                 'county_code': city[8], 'cc2': city[9],
                 'admin1_code': city[10], 'admin2_code': city[11],
                 'admin3_code': city[12], 'admin4_code': city[13],
                 'population': city[14], 'elevation': city[15],
                 'dem': city[16], 'timezone': city[17],
                 'modification_date': city[18][:-1]}
    return city_dict


async def info_by_id(request):
    """
    Метод принимает идентификатор geonameid и возвращает информацию о городе.
    """
    try:
        geonameid = int(request.query['id'])

        # Если введенный клиентом geonameid больше максимального или меньше минимального geonameid, лежащего в
        # базе данных, то сервер отправляет ответ со статусом 500
        if geonameid < int(cities_list[0][0]) or geonameid > int(cities_list[-1][0]):
            response_obj = {'status': 'failed', 'message': "Couldn't find any city by this id"}
            return web.Response(text=json.dumps(response_obj), status=500)

        # нужный элемент находится посредством алгоритма бинарного поиска
        left_b = -1
        right_b = 201177
        while left_b < right_b - 1:
            mid = (left_b + right_b) // 2
            if int(cities_list[mid][0]) < geonameid:
                left_b = mid
            else:
                right_b = mid

        message = make_a_city_dict(cities_list[right_b])
        response_obj = {'status': 'success', 'message': message}
        return web.Response(text=json.dumps(response_obj, ensure_ascii=False), status=200)
    except Exception as e:
        response_obj = {'status': 'failed', 'message': 'Parameter id is not define: {0}'.format(str(e))}
        return web.Response(text=json.dumps(response_obj), status=500)


async def cities_page(request):
    """
    Метод принимает страницу и количество отображаемых на странице городов и возвращает список городов с их информацией.
    """
    try:
        page = int(request.query['page'])
        cnt_cities_on_page = int(request.query['count'])

        all_cities = 201177

        # Проводится проверка корректности введенных клиентом данных
        if cnt_cities_on_page > all_cities or cnt_cities_on_page == 0:
            response_obj = {'status': 'failed', 'message': "This page doesn't exist:"
                                                           " something wrong with counting cities on the page"}
            return web.Response(text=json.dumps(response_obj), status=200)

        cnt_pages = ceil(all_cities / cnt_cities_on_page)

        # номер последнего элемента страницы предыдущей искомой
        end_of_previous_page = cnt_cities_on_page * (page - 1)  # (начало отсчеты индексируется единицей)

        result_page = []

        # проводится проверка корректности введенных данных
        if page <= cnt_pages and page != 0:
            if end_of_previous_page + cnt_cities_on_page <= all_cities:
                for i in range(cnt_cities_on_page):
                    result_page.append(make_a_city_dict(cities_list[end_of_previous_page + i]))
            else:
                # исключительный случай обработки вывода последней страницы
                for i in range(all_cities - end_of_previous_page):
                    result_page.append(make_a_city_dict(cities_list[end_of_previous_page + i]))
        else:
            response_obj = {'status': 'failed', 'message': "This page doesn't exist: "
                                                           "something wrong with the number of page"}
            return web.Response(text=json.dumps(response_obj), status=200)

        response_obj = {'status': 'success', 'message': result_page}
        return web.Response(text=json.dumps(response_obj, ensure_ascii=False), status=200)
    except (ValueError, KeyError):
        response_obj = {'status': 'failed', 'message': 'something wrong with input data'}
        return web.Response(text=json.dumps(response_obj), status=200)


async def find_a_correct_city(name):
    """
    Вспомогательная функция; вовзращает город, найденный по альтернативному имени.
    """
    result = [i for i, city in enumerate(cities_list) if name in city[3].split(',')]
    max_population = -1
    cities_list_index = None
    for i in result:
        if int(cities_list[i][14]) > max_population:
            max_population = int(cities_list[i][14])
            cities_list_index = i
    city1 = make_a_city_dict(cities_list[cities_list_index])
    return city1


async def comparison(request):
    """
    Метод принимает названия двух городов (на русском языке) и получает информацию о найденных городах, а также
    дополнительно: какой из них расположен севернее и одинаковая ли у них временная зона (когда несколько городов имеют
    одно и то же название, разрешать неоднозначность выбирая город с большим населением; если население совпадает,
    брать первый попавшийся)
    """
    try:
        name1 = request.query['city1']
        name2 = request.query['city2']
        city1 = await find_a_correct_city(name1)
        city2 = await find_a_correct_city(name2)

        if city1.get('latitude') > city2.get('latitude'):
            northern = 'city1'
        else:
            northern = 'city2'

        if city1.get('timezone') == city2.get('timezone'):
            same_timezone = True
        else:
            same_timezone = False
        response_obj = {'status': 'success',
                        'message': {'city1': city1, 'city2': city2, 'northern': northern,
                                    'same_timezone': same_timezone}
                        }
        return web.Response(text=json.dumps(response_obj, ensure_ascii=False), status=200)
    except Exception as e:

        response_obj = {'status': 'failed', 'message': "something wrong with input data or city "
                                                       "with this name doesn't exist in the database: {}".format(str(e))
                        }
        return web.Response(text=json.dumps(response_obj), status=200)


app = web.Application()
app.router.add_get('/api/v1/info_by_id', info_by_id)
app.router.add_get('/api/v1/cities_page', cities_page)
app.router.add_get('/api/v1/comparison', comparison)

web.run_app(app, port=8000)
