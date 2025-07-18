import pandas as pd

df=pd.read_csv(r"C:\Users\Administrator\Desktop\test\address.csv")
url = df.loc[0, 'url']
data=df.loc[0,'data']
print(data)