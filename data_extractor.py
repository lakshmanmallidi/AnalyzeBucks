from pickle import load
from datetime import datetime
from time import mktime

def StateBankIndia(raw_data):
    def convert_date(raw_date):
        return int(mktime(datetime.strptime(raw_date, "%d %b %Y").timetuple()))

    formated_data = [row.split("\t") for row in raw_data.split("\n")]
    final_data = []
    row_num = 20
    while True:
        if(len(formated_data[row_num]) >= 5):
            transaction_date = convert_date(formated_data[row_num][0])
            details = formated_data[row_num][2].strip()
            if(formated_data[row_num][4] != " "):
                debit_amount = float(formated_data[row_num][4].replace(",", ""))
            else:
                debit_amount = ""
            if(formated_data[row_num][5] != " "):
                credit_amount = float(formated_data[row_num][5].replace(",", ""))
            else:
                credit_amount = ""
            if(formated_data[row_num][6] != " "):
                balance_amount = float(formated_data[row_num][6].replace(",", ""))
            else:
                balance_amount = ""
            final_data.append(
                (transaction_date, details, debit_amount, credit_amount, balance_amount))
        else:
            break
        row_num = row_num+1
    return final_data

def factory(bank_name):
    if(bank_name=='sbh'):
        return StateBankIndia