# -*- coding: utf-8 -*-
"""
@ author: znj
@ datetime: 2020/12/28 15:51
@ software: PyCharm
"""
import json
import math
import time
import traceback

import pika
import pymap3d as pm


#
from interval_util import IntervalUtil

FILE_WRITE_FLAG = False
fo = open("apa_simu_record.txt", "a+")

interval_util = IntervalUtil()


def cal_obu_time(cnt, sec):
    a = sec * 60
    a %= 128
    t = (cnt + 128 - a) % 128
    return int((sec + t / 60) * 1000)


def send_data(msg):
    json_str = msg
    print(json_str)
    if FILE_WRITE_FLAG:
        fo.write(json_str + '\n')
    channel_send.basic_publish(
        # 融合数据
        exchange="ord-multi-roadside-fusion-result-exchange-private",
        routing_key="",  # 写明将消息发送给队列balance
        body=json_str,  # 要发送的消息
        properties=pika.BasicProperties(delivery_mode=2, )  # 设置消息持久化(持久化第二步)，将要发送的消息的属性标记为2，表示该消息要持久化
    )
    # s = {"id": "0000001", "refPos": None, "time": int(1000*time.time()), "details": []}
    # channel_send.basic_publish(
    #     # 融合数据
    #     exchange="ord-traffic-info-exchange",
    #     routing_key="",  # 写明将消息发送给队列balance
    #     body= json.dumps(s),  # 要发送的消息
    #     properties=pika.BasicProperties(delivery_mode=2, )  # 设置消息持久化(持久化第二步)，将要发送的消息的属性标记为2，表示该消息要持久化
    # )
    # channel_send.basic_publish(
    #     # 融合数据
    #     exchange="ord-local-test-rosbag-obu-data",
    #     routing_key="",  # 写明将消息发送给队列balance
    #     body=json_str,  # 要发送的消息
    #     properties=pika.BasicProperties(delivery_mode=2, )  # 设置消息持久化(持久化第二步)，将要发送的消息的属性标记为2，表示该消息要持久化
    # )


def enu2wgs(xEast, yNorth, zUp=0):
    """
    convert localENU to wgs-84
    :param xEast: localENU x
    :param yNorth: localENU y
    :param zUp: localENU z
    :return: list [longitude, latitude] in wgs-84
    """
    # 手动指定坐标系中心坐标，数据来自xml文件的<header><userData>,需要手动选择
    # center coordinates
    # dongfeng 东风
    # lat0 = 30.4460710869714  # deg
    # lon0 = 114.076573527225  # deg
    # h0 = -3.98714209726941  # meters
    # # # chuangxingang 创新港
    # lat0 = 31.2529141563274
    # lon0 = 121.61192536354
    # h0 = -9.9999649
    # #chuangao
    # lat0 = 31.0341639478943
    # lon0 = 103.531597321627
    # h0 = 12.035581415073
    #chuangao new
    # lat0 = 31.0292557537742
    # lon0 = 103.533821072173
    # h0 = 9.3211894177424
    #youdu
    # lat0 = 31.2529141563274
    # lon0 = 121.61192536354
    # h0 = 0
    # apa
    lat0 = 100
    lon0 = 30
    h0 = 0
    # enu_to_84
    lat_enu, lon_enu, h_enu = pm.enu2geodetic(xEast, yNorth, zUp, lat0, lon0, h0, deg=True)
    return lon_enu, lat_enu


def loc_format(lon, lat):
    format_lon, format_lat = enu2wgs(lon, lat)
    return format_lon, format_lat


def getDestination(lon1, lat1, brng, distance):
    R = 6371  # Radius of the Earth in Km
    distance = distance / 1000  # change distance from m to km
    # 将角度转为弧度
    # brng为弧度
    lat1 = math.radians(lat1)
    lon1 = math.radians(lon1)
    lat2 = math.asin(math.sin(lat1) * math.cos(distance / R) +
                     math.cos(lat1) * math.sin(distance / R) * math.cos(brng))
    lon2 = lon1 + math.atan2(math.sin(brng) * math.sin(distance / R) * math.cos(lat1),
                             math.cos(distance / R) - math.sin(lat1) * math.sin(lat2))
    lat2 = math.degrees(lat2)
    lon2 = math.degrees(lon2)
    return lon2, lat2


def data_format(data_list):
    if not data_list:
        return []
    result_list = []
    for data in data_list:
        obj = {}
        if data["type"] in ('main vehicle', 'car'):
            obj["ptcType"] = 1
        if data["type"] in ('pedestrian'):
            obj["ptcType"] = 3
        if data["type"] in ('bicycle'):
            obj["ptcType"] = 2
        if data["type"] in ('unknown'):
            obj["ptcType"] = 4
        else:
            obj["ptcType"] = 1
        obj["ptcId"] = str(data["id"])
        obj["mepid"] = 0
        obj["obuId"] = str(data["id"])
        obj["plateNo"] = data["license_plate"]
        obj["heading"] = int((math.degrees(data["arctan"]["hdq"]) / 0.0125))
        lon, lat = data["location"]["longitude"], data["location"]["latitude"]
        # print(lon,lat)
        linfo = interval_util.locate(lon,lat)

        # if obj["ptcType"] == 3:
        #     lon, lat = loc_format(data["pos.lon"], data["pos.lat"])
        # else:
        #     lon_1, lat_1 = loc_format(data["pos.lon"], data["pos.lat"])
        #     hdq = math.radians(obj["heading"] * 0.0125)
        #     lon, lat = getDestination(lon_1, lat_1, hdq, data["size.length"] * 3 / 10)

        obj["pos"] = {"longitude": round((0+lon) * 10000000), "latitude": round((0+lat) * 10000000),
                      "altitude": int(data["location"]["altitude"] / 0.1)}
        obj["speed"] = int(data["speed"] * 50)
        obj["size"] = {"length": int(100 * data["pose"]["length"]), "width": int(100 * data["pose"]["width"]),
                       "height": int(20 * data["pose"]["height"])}
        obj["vehicleClass"] = 10
        obj["speedhdq"] =  0
        # obj["roadId"] = 0
        # obj["laneId"] = 0
        obj["roadId"] = linfo.road_id
        obj["laneId"] = linfo.lane_id
        obj["linfo"] = {"linfo_hdg": linfo.hdg, "linfo_s": linfo.s, "linfo_width": linfo.width}
        obj["intervals"]= []
        # obj["extend"] = {"accuracy": {"pos": data["accuracy.pos"], "elevation": data["accuracy.elevation"]},
        #                  "transmission": data["transmisson"],
        #                  "angle": data["angle"],
        #                  "motionCfd": {"speedCfd": data["motionCfd.speedCfd"],
        #                                "headingCfd": data["motionCfd.headingCfd"],
        #                                "steerCfd": data["motionCfd.steerCfd"]},
        #                  "accelSet": {"lng": data["accelSet.lon"], "lat": 0,
        #                               "vert": data["accelSet.vert"], "yaw": data["accelSet.yaw"]},
        #                  "brakes": {"breakPadel": data["brakes.brakePadel"], "wheelBrakes": data["brakes.wheelBrakes"],
        #                             "traction": data["brakes.traction"], "abs": data["brakes.abs"],
        #                             "scs": data["brakes.scs"], "auxBrakes": data["brakes.auxBrakes"]},
        #                  "saftvExt": {}}

        result_list.append(obj)
    return result_list


def mq_callback(ch, method, properties, body):
    """callback function for successful consuming of channel1
    """
    global global_count
    ch.basic_ack(delivery_tag=method.delivery_tag)
    receive_data = body.decode()
    receive_data = json.loads(receive_data)

    print(receive_data)
    receive_data_obj_list = data_format(receive_data["device_data"][0]["object"])
    # # for obu_data in receive_data_obu_list:
    #     # if obu_data["obuId"] == "0" or obu_data["obuId"] == 0:
    #     #     global_count += 1
    #     #     if global_count < 5:
    #     #         continue
    #     #     else:
    #     #         global_count = 0
    #     # if obu_data["vehicleClass"] not in (0,1):
    #     #     continue
    #     # timestamp = cal_obu_time(receive_data["obu_list"][0]["msgCnt"], receive_data["obu_list"][0]["secMark"])
    timestamp = receive_data['time']
    # [{"ptcType": 1, "plateNo": null, "ptcId": "9524", "size": {"length": 461, "width": 179, "height": 30}, "pos": {"longitude": 1035342135, "latitude": 310269582, "altitude": 90740}, "heading": 14800, "speed": 0, "obuId": "headCar1", "vehicleClass": 10, "speedhdq": 0, "roadId": 0, "laneId": 0, "intervals": []}]
    msg = {"id": "00000001", "refPos": {"longitude": 0, "latitude": 0, "altitude": 0}, "rsuId": "rsu0", "timestamp": timestamp, "source": 0, "deviceId": None, "fuseSources": None, "dataModel": 3, "participants": receive_data_obj_list}
    # # print(msg)
    send_data(json.dumps(msg))


def init_mq():
    result = channel_receive.queue_declare(exclusive=True, queue='')
    queue_name = result.method.queue
    channel_receive.queue_bind(
        exchange=exchange_name, queue=queue_name,
        routing_key="")

    print('[*] Writing for logs. To exit press CTRL+C.')
    # 开始依次消费balance队列中的消息
    channel_receive.basic_consume(queue=queue_name, on_message_callback=mq_callback, auto_ack=False)
    print('[*] Waiting for messages. To exit press CTRL+C')
    channel_receive.start_consuming()  # 启动消费


username = 'fds-ft'
pwd = "Fds-ft@2020"
ip_addr = '172.31.240.139'
port_num = 5672
v_host = 'cg-ord'
v_host = 'ord-ft'
# v_host = 'cgtx-dev'


username_sit = 'fds-sit'
pwd_sit = "Fds-sit@2020"
while True:
    try:
        global_count = 0
        credentials = pika.PlainCredentials(username, pwd)
        credentials_sit = pika.PlainCredentials(username_sit, pwd_sit)
        connections_receive = pika.BlockingConnection(pika.ConnectionParameters(ip_addr, port_num, 'ord-ft', credentials))
        channel_receive = connections_receive.channel()
        # connections_send = pika.BlockingConnection(pika.ConnectionParameters(ip_addr, port_num, 'fds-sit', credentials_sit))
        connections_send = pika.BlockingConnection(
            pika.ConnectionParameters(ip_addr, port_num, 'ord-ft', credentials))
        # connections_send = pika.BlockingConnection(pika.ConnectionParameters('10.202.8.151', port_num, 'ord-ft', credentials))
        channel_send = connections_send.channel()
        # channel_send.exchange_declare(exchange="cg_dev_exchange_msg", exchange_type='topic', durable='true')
        exchange_name = 'risk_test'
        channel_receive.exchange_declare(exchange=exchange_name, exchange_type='fanout', durable='true')
        # 导入后融合数据
        init_mq()
    except Exception as e:
        # print(connections_send)
        # print(connections_receive)
        print(e)
        try:
            connections_receive.close()
            connections_send.close()
        finally:
            print("close all connection")
            time.sleep(2)
        print("ERROR:",e)
        print("traceback.format_exec():\n%s" % traceback.format_exc())
