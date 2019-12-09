import os,pandas
from CommonFunction.ExcelReading import validate_DataFrameCol,validate_DataFrameColType,read_Excel

list_col = ["Number of TA={}".format(x) for x in range(64)]

# percentage_list = [0.95,0.97,0.98,0.985,0.995]

def getTaBoundry(series,percentage):
    if series['Ta_total'] == 0:
        return 0
    else:
        total = series['Ta_total']
        ta_list = series[list_col].tolist()
        for index,value in enumerate(ta_list):
            sum_temp = sum(ta_list[:index])
            if sum_temp/total >= percentage:
                return index
        return len(ta_list)



def main_getTAcov(filepath,sheetlist,percentage_list):
    output_file = '_TaBoundry'.join(os.path.splitext(filepath))
    DataFrame = read_Excel(filepath,sheetlist)
    if not DataFrame.empty and validate_DataFrameCol(DataFrame,list_col):
        for percentage in percentage_list:
            TaData = DataFrame[list_col]
            DataFrame['Ta_total'] = TaData.apply(lambda x:x.sum(),axis = 1)

            DataFrame['maxTA for {}'.format(percentage)] = DataFrame.apply(getTaBoundry,args = (percentage,),axis = 1)
        # print(DataFrame.columns)
        DataFrame.to_excel(output_file)
        return DataFrame
    else:
        return pandas.DataFrame(columns=['Empty'])

if __name__ == '__main__':
    main_getTAcov(r'C:\Users\10225167\Desktop\History Performance_CellFunction(GSM)_20191104165749.xlsx',
                  ['sheet1'],
                  [0.95,0.97,0.98,0.985,0.995])