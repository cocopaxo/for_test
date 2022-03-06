import pandas as pd
import numpy as np
from matplotlib import pyplot as plt

plt.rcParams['font.sans-serif'] = ['SimHei']  # 显示中文标签
plt.rcParams['axes.unicode_minus'] = False

def analyse_log(logfile):
    #读取logfile文件
    with open(logfile) as file:
        ttc_list = []
        for log_msg in file:
            if 'ttc_dis_risk' in log_msg:
                total_msg = log_msg.replace("\'", "\"")
                total_msg = total_msg[total_msg.index('ttc_dis_risk: ('):].lstrip('ttc_dis_risk: (').replace(")", "").rsplit()
                if total_msg[-1] != -1.0:
                    ttc_msg = float(total_msg[1].replace(",", ""))
                    if (ttc_msg >=0) & (ttc_msg <=5.0):
                        ttc_list.append(ttc_msg)



        ttc_pd = pd.DataFrame(ttc_list, columns=['ttc'])
        print(ttc_pd)

        plt.plot(range(len(ttc_list)),ttc_list,color = 'r')
        # plt.scatter(range(len(ttc_list)), ttc_list, color='b')
        plt.title("风险等级变化", fontdict={'size': 16})
        plt.xlabel('帧数(fps)', fontdict={'size': 14})
        plt.ylabel('ttc', fontdict={'size': 14})
        plt.legend(['车辆1'])
        plt.show()











if __name__ == '__main__':

    analyse_log(logfile=r'C:\Users\Q1\Desktop\log\debug2.txt')
