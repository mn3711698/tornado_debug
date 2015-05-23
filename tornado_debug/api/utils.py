# coding:utf8


def get_sorted_data(datas):
    """
    data: {name1: {count:0, time:0}, }
    return [{name: name1, count:0, time:0},...]
    """
    func = []
    for name, data in datas.items():
        data['time'] = round(data['time']*1000, 2)
        func.append({'name': name, 'count': data['count'], 'time': data['time']})
    func = sorted(func, key=lambda x: x['time'], reverse=True)
    return func
