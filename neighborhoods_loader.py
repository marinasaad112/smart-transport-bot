import pandas as pd

def load_neighborhoods():
    data = {}
    xls = pd.ExcelFile("neighborhoods.xlsx")
    for sheet in xls.sheet_names:
        df = pd.read_excel(xls, sheet)
        neighborhoods = df.iloc[:, 0].dropna().tolist()
        data[sheet] = neighborhoods
    return data

NEIGHBORHOODS = load_neighborhoods()
