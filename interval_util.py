'''
Created on 2021年5月24日

@author: tang
'''
import logging
import threading
from os import terminal_size
import time

from OnLane import LaneInfo
import pickle
from coord_trans import CoordTrans

from geopy.distance import geodesic

import math

INTERVAL_TYPE_TEAM = 1
INTERVAL_TYPE_OBSTACLE = 2
INTERVAL_TYPE_END = 3
INTERVAL_TYPE_MID = 4


class PointError(Exception):
    def __init__(self, error_info):
        super().__init__(self)  # 初始化父类
        self.errorinfo = error_info

    def __str__(self):
        return self.errorinfo


class IntervalUtil():

    def __init__(self):
        self.coord = CoordTrans()
        # 暂时不考虑十字路口一个多个road的情况

        self.memory_cache_lock = threading.Lock()
        self.line_info = LaneInfo()

    def cal_utm(self, lon, lat):
        if isinstance(lon, int):
            lon = lon / 10 ** 7
        if isinstance(lat, int):
            lat = lat / 10 ** 7
        utmx, utmy, utm_zone = self.coord.gps2utm(lon, lat)
        return utmx, utmy

    def locate(self, lon,lat, map_name='Boshutm'):
        # print("locate", map_name)
        x1, y1 = self.cal_utm(lon, lat)
        linfo = self.line_info
        linfo.get_point(x1, y1, map_name)
        # print((start_time_2 - start_time_1) * 1000)
        if linfo.road_id == 0:
            print('point not in the map!')
            # raise PointError(f'point not in the map!,{part.longitude}, {part.latitude}, {part}')
            #  logging.info(f'point not in the map!,{part.longitude}, {part.latitude}, {part}')
        # part.linfo = linfo
        return linfo

    # 获取两个交通参与者之间间隔的道路，
    # 判断交通参与者的前后关系，根据车道，如果在同一车道则为0   
    # def get_interval_road(self, part1, part2):
    #     interval_road_arr = []
    #     is_before = 0
    #     part2_road_id = part2.linfo.road_id
    #     part1_road_id = part1.linfo.road_id
    #     # 如果两个点在弯道位置 则获取并排的某个弯道进行计算
    #     if part1_road_id in self.corner_dic:
    #         part1_road_id = self.corner_dic[part1_road_id]
    #     if part2_road_id in self.corner_dic:
    #         part2_road_id = self.corner_dic[part2_road_id]
    #     part2_road_idx = self.road_link.index(part2_road_id)
    #     part1_road_idx = self.road_link.index(part1_road_id)
    #     # if part2.linfo.road_id == part1.linfo.road_id:
    #     #     pass
    #     if part2_road_idx < part1_road_idx:
    #         interval_road_arr = self.road_link[part2_road_idx + 1: part1_road_idx]
    #         is_before = 1
    #     if part2_road_idx > part1_road_idx:
    #         interval_road_arr = self.road_link[part1_road_idx + 1: part2_road_idx]
    #         is_before = -1
    #     return interval_road_arr, is_before

    #   计算两个交通参与者之间的距离
    #   part1作为被比较方，part2作为比较方，part1在前，输出之为正值，part1在后输出之为负值
    # def cal_part_distance(self, part1, part2):
    #     interval_road, is_before = self.get_interval_road(part1, part2)
    #     distance = 0
    #     if is_before == 0:
    #         distance = part2.linfo.remaining_s - part1.linfo.remaining_s
    #     else :
    #         for road in interval_road:
    #             distance = distance + LaneInfo.data['road'][road]['length']
    #         if is_before == 1:
    #             distance = distance + (LaneInfo.data['road'][part1.linfo.road_id][
    #                                        'length'] - part1.linfo.remaining_s + part2.linfo.remaining_s)
    #         else:
    #             distance = 0 - (distance + (LaneInfo.data['road'][part2.linfo.road_id][
    #                                             'length'] - part2.linfo.remaining_s + part1.linfo.remaining_s))
    #     return distance

    #   计算交通参与者与指点点的的距离
    #   point作为被比较方，交通参与者作为比较方，point在前，输出之为正值，point在后输出之为负值
    # def cal_point_part_distance(self, point, part):
    #     participant = EdgeFusionObjects(ptc_id=-1, ptc_type=-1, ptc_no='-1', height=0, length=0, width=0, altitude=0,
    #                                     heading=0, speed=0, longitude=point.longitude, latitude=point.latitude)
    #     if not hasattr(point, 'linfo'):
    #         self.locate(participant)
    #         point.linfo = participant.linfo
    #     else:
    #         participant.linfo = point.linfo
    #     if not hasattr(part, 'linfo'):
    #         self.locate(part)
    #     distance = self.cal_part_distance(participant, part)
    #     return distance

    def gen_team_dic(self, participants: list):
        for part in participants:
            try:
                self.locate(part, None)
            except PointError:
                logging.info(PointError)
            #   初始化intervals
            part.intervals = []
            part.road_id = part.linfo.road_id
            part.lane_id = part.linfo.lane_id

    def cal_locate(self, participants: list):
        print("try lock in cal intervals")
        self.memory_cache_lock.acquire()
        print("get lock in cal intervals")
        try:
            # self.cal_edge_intervals(participants)
            self.gen_team_dic(participants)
        finally:
            self.memory_cache_lock.release()
        for part in participants:
            if hasattr(part, 'intervals') and len(part.intervals) > 0 :
                part.intervals.pop(0)


i = IntervalUtil()
