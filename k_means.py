
# 导入第三方包
# coding: utf-8
from sklearn.cluster import KMeans
from sklearn import preprocessing
import numpy as np
import matplotlib.pyplot as plt
import pandas as pd

# 随机生成两组二元正态分布随机数
np.random.seed(1234)
mean1 = [0.5, 0.5]
cov1 = [[0.3, 0], [0, 0.1]]
x1, y1 = np.random.multivariate_normal(mean1, cov1, 5000).T

mean2 = [0, 8]
cov2 = [[0.8, 0], [0, 2]]
x2, y2 = np.random.multivariate_normal(mean2, cov2, 5000).T

# 绘制两组数据的散点图
plt.rcParams['axes.unicode_minus'] = False
plt.scatter(x1, y1)
plt.scatter(x2, y2)
# 显示图形
plt.show()

# 将两组数据集汇总到数据框中
X = pd.DataFrame(np.concatenate([np.array([x1, y1]), np.array([x2, y2])], axis=1).T)
X.rename(columns = {0:'x1',1:'x2'}, inplace = True)
# 自定义函数的调用


def kmeans_outliers(data, clusters, is_scale = True):
    # 指定聚类个数，准备进行数据聚类
    kmeans = KMeans(n_clusters=clusters)
    # 用于存储聚类相关的结果
    cluster_res = []

    # 判断是否需要对数据做标准化处理
    if is_scale:
        std_data = scale(data) # 标准化
        kmeans.fit(std_data)  # 聚类拟合
        # 返回簇标签
        labels = kmeans.labels_
        # 返回簇中心
        centers = kmeans.cluster_centers_

        for label in set(labels):
            # 计算簇内样本点与簇中心的距离
            diff = std_data[np.array(labels) == label,] - \
                   - np.array(centers[label])
            dist = np.sum(np.square(diff), axis=1)
            # 计算判断异常的阈值
            UL = dist.mean() + 3*dist.std()
            # 识别异常值，1表示异常，0表示正常
            OutLine = np.where(dist > UL, 1, 0) 
            raw_data = data.loc[np.array(labels) == label,]
            new_data = pd.DataFrame({'Label':label,'Dist':dist,'OutLier':OutLine})
            # 重新修正两个数据框的行编号
            raw_data.index = new_data.index = range(raw_data.shape[0])
            # 数据的列合并
            cluster_res.append(pd.concat([raw_data,new_data], axis = 1))
    else:
        kmeans.fit(data)  # 聚类拟合
        # 返回簇标签
        labels = kmeans.labels_
        # 返回簇中心
        centers = kmeans.cluster_centers_

        for label in set(labels):
            # 计算簇内样本点与簇中心的距离
            diff = np.array(data.loc[np.array(labels) == label,]) - \
                   - np.array(centers[label])

            dist = np.sum(np.square(diff), axis=1)
            UL = dist.mean() + 3*dist.std()
            OutLine = np.where(dist > UL, 1, 0)
            raw_data = data.loc[np.array(labels) == label,]
            new_data = pd.DataFrame({'Label':label,'Dist':dist,'OutLier':OutLine})
            raw_data.index = new_data.index = range(raw_data.shape[0])
            cluster_res.append(pd.concat([raw_data,new_data], axis = 1))
    # 返回数据的行合并结果    
    return pd.concat(cluster_res)

# 调用函数，返回异常检测的结果
res = kmeans_outliers(X,2,False)
# res
# 绘图
sns.lmplot(x="x1", y="x2", hue='OutLier', data=res,
           fit_reg=False, legend=False)
plt.legend(loc='best')
plt.show()