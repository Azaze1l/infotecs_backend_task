from aiohttp import web
import json
from math import ceil
"""
TODO:
Реализованный сервер должен предоставлять REST API сервис со следующими методами:
1.	Метод принимает идентификатор geonameid и возвращает информацию о городе.
2.	Метод принимает страницу и количество отображаемых на странице городов и возвращает список городов с их информацией. 
3.	Метод принимает названия двух городов (на русском языке) и получает информацию о найденных городах, а также 
    дополнительно: какой из них расположен севернее и одинаковая ли у них временная зона (когда несколько городов имеют 
    одно и то же название, разрешать неоднозначность выбирая город с большим населением; если население совпадает, 
    брать первый попавшийся)
"""

file = open('RU.txt', 'r', encoding='utf-8')
cities_list = []
for line in file:
    cities_list.append(line.split('\t'))


def make_a_city_dict(city):
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
        if geonameid < int(cities_list[0][0]) or geonameid > int(cities_list[-1][0]):
            response_obj = {'status': 'failed', 'message': "Couldn't find any city by this id"}
            return web.Response(text=json.dumps(response_obj), status=500)

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
        if cnt_cities_on_page > all_cities or cnt_cities_on_page == 0:
            response_obj = {'status': 'failed', 'message': "This page doesn't exist:"
                                                           " something wrong with count of cities on page"}
            return web.Response(text=json.dumps(response_obj), status=200)

        cnt_pages = ceil(all_cities/cnt_cities_on_page)
        end_of_previous_page = cnt_cities_on_page*(page-1)

        result_page = []
        if page <= cnt_pages and page != 0:
            if end_of_previous_page + cnt_cities_on_page <= all_cities:
                for i in range(cnt_cities_on_page):
                    result_page.append(make_a_city_dict(cities_list[end_of_previous_page + i]))
            else:
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


async def comparison(request):
    city1 = request.query('city1')
    city2 = request.query('city2')
    pass


app = web.Application()
app.router.add_get('/api/v1/info_by_id', info_by_id)
app.router.add_get('/api/v1/cities_page', cities_page)

web.run_app(app, port=8000)
