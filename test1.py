import openpyxl
import pandas as pd

sheet = pd.read_excel('data.xlsx',sheet_name='Sheet1')
list1 = sheet['姓名'].tolist()
j = 0
for name in list1:
    if len(name) == 3:
        j += 1
print(j)


x0 = 1
n = 10
c = 100
for i in range(n):
    x1 = (c/x0 + x0)/2
    x0 = x1
print(x0)


