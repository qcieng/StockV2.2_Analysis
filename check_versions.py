
import numpy
print(f"Numpy: {numpy.__version__}")
import pandas
print(f"Pandas: {pandas.__version__}")
try:
    import akshare
    print(f"Akshare: {akshare.__version__}")
except:
    print("Akshare failed")

print("Importing data_fetcher...")
import data_fetcher
print("Data fetcher imported")
