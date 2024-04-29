from commbank import Client
from commbank.parser import parse_api_transactions
import base64
from datetime import datetime
from pdb import set_trace as bp
import json
import os
import tkinter as tk
import sys
from tkinter import simpledialog
from tkinter import messagebox

if getattr(sys, 'frozen', False):
        work_folder = os.path.dirname(sys.executable)
elif __file__:
        work_folder = os.path.dirname(__file__)
#work_folder="C:\\Users\\92931\\Downloads\\commbank-api-main\\commbank-api-main\\"
renters_file="renters.cfg"
renters=[]#A list of all the renters.

def query_transactins(username,password):
        global work_folder
        all_transactions=[]
        client = Client(timeout=10)
        USERNAME=username
        PASSWORD=password
        #USERNAME=input("Username:")
        #PASSWORD=input("password:")
        client.login(USERNAME, PASSWORD)
        #transactions=client.transactions()
        #print(transactions)
        accounts=client.accounts()
        #for account in accounts:
        #  print(account.bsb,account.number)
        
        transactions=""
        message_str="Select among below accounts:\n"
        account_i=0
        for account in accounts:
            message_str+=str(account_i)+str(account)+"\n"
            account_i+=1
        account_i = int(simpledialog.askstring("Input", message_str))    
        print("account_i={"+str(account_i)+"}")
        #account_i=int(input("Please select which account to explore:\n"))
        #Then in the return result, we get the current transctions' last date 
        today_date = datetime.today().date()
        last_date=today_date.strftime("%Y-%d-%m")
        last_tran=transactions
        while transactions!=[]:#If you check before 2 years' transaction, it will return []
                #print("transactions:",transactions)
                transactions=client.transactions(accounts[account_i])
                if transactions==last_tran:#Same tran record also means reaching 2 years limit
                  break
                #print("first:",transactions[0])
                #print("last:",transactions[-1])
                add_tran(all_transactions,transactions)
                #We need to find the earliest transaction's date, and transcation ID
                first_date,first_transcode=find_first_transaction(transactions)
                #bp()
                accounts[account_i].link=change2first_date(accounts[account_i].link,last_date,first_date)
                last_date=first_date
                last_tran=transactions
        
        json_file_path = work_folder+"\\"+str(today_date)+".json"
        print("json_file_path:"+json_file_path)
        messagebox.showinfo("Message", "Transactions has been downloaded into "+json_file_path)
        with open(json_file_path, 'w') as json_file:
            json.dump(all_transactions, json_file)        
                

def find_first_transaction(transactions):
    return transactions[-1]['date'][:10],transactions[-1]['trancode']

def add_tran(all_transactions,transactions):
    for tran in transactions:
        if tran not in all_transactions:
            all_transactions.append(tran)

#Decode a url link, and replace the last date with the first date. Then encode that url.
def change2first_date(account_link,last_date,first_date):
    pageKey="&pagingKey="
    pageKey_template="E2E21F8404021EDEAFE14550CA698003,001,2022-05-30,205.95,AUD,CR,20240130005448.1950751,SAP,%3D"
    if account_link.find(pageKey)>-1:
        updated_link=""
        pagingKey=account_link.split(pageKey)[1]
        decoded_bytes = base64.b64decode(pagingKey)
        decoded_string = decoded_bytes.decode('utf-8')
        decoded_string=decoded_string.replace(last_date,first_date)
        
        encoded_bytes = base64.b64encode(decoded_string.encode('utf-8'))
        encoded_string = encoded_bytes.decode('utf-8')
        updated_link=account_link.split(pageKey)[0]+pageKey+encoded_string
        return updated_link
    else:
        pre_part=pageKey_template.split(',')[:2]
        parts=pageKey_template.split(',')[3:]
        new_pagekey=pre_part[0]+","+pre_part[1]+","+first_date+","
        for part in parts:
            new_pagekey+=part+","
        new_pagekey=new_pagekey[:-1]
        encoded_bytes = base64.b64encode(new_pagekey.encode('utf-8'))
        encoded_string = encoded_bytes.decode('utf-8')
        updated_link=account_link+pageKey+encoded_string
        return updated_link

def read_renters(file_path):
    with open(file_path, 'r') as cfg_file:
      cfg_content = cfg_file.read()
      lines = cfg_content.split('\n')
      return lines

#In a folder, there might be multiple json files, each may be queried in differenct days
#for all the 2 years-period transactions. We need to merge them together to form a json
def read_jsons(folder_path):
        files = os.listdir(folder_path)
        # Filter JSON files
        json_files = [file for file in files if file.endswith('.json')]
        
        # Read JSON files
        json_data = []
        
        for file_name in json_files:
            file_path = os.path.join(folder_path, file_name)
            with open(file_path, 'r') as json_file:
                rows = json.load(json_file)
                for row in rows:
                    if row not in json_data:
                        json_data.append(row)
        return json_data  

#For each renter, we need to extract his payment record
def audit_renters(renters,json_data):
    records=[]
    
    for i in renters:
        records.append([])
    for tran in json_data:
        for renter_i in range(0,len(renters)):
            if renters[renter_i].lower() in tran['payee'].lower():
                simple_tran={}
                simple_tran['date']=tran['date']
                simple_tran['amount']=tran['amount']
                records[renter_i].append(simple_tran)
    return records     

#To neatly print each renter and their transaction history
def print_audit(renters,result):
    print_str=""
    for renter,recs in zip(renters,result):
        print("Renter "+renter+": ")
        print_str+="Renter "+renter+": \n"
        for rec in recs:
            print("     "+str(rec))
            print_str+="     "+str(rec)+"\n"
        print("--------------------------------------------")   
        print("--------------------------------------------")
        print_str+="--------------------------------------------\n"
        print_str+="--------------------------------------------\n"
        audit_path=work_folder+"\\audit.txt"
    messagebox.showinfo("Message", "Audit has been written into "+audit_path)
    with open(audit_path, 'w') as file:
        file.write(print_str)
    #messagebox.showinfo("Message", print_str)


def submit_data(option_entry,username_entry,pass_entry):
    action=option_entry.get()
    username=username_entry.get()
    password=pass_entry.get()
    if action=='1':
            renters=read_renters(work_folder+"\\"+renters_file)
            json_data=read_jsons(work_folder)
            result=audit_renters(renters,json_data)
            print_audit(renters,result)
    elif action=='2':
            query_transactins(username,password)

def main():
        root = tk.Tk()
        root.title("Input Panel")

        tk.Label(root, text="Please select options: 1.Audit 2.Extract transactions\n").grid(row=0, column=0, padx=5, pady=5)
        option_entry = tk.Entry(root)
        option_entry.grid(row=0, column=1)

        tk.Label(root, text="Customer ID:").grid(row=1, column=0, padx=5, pady=5)
        username_entry = tk.Entry(root)
        username_entry.grid(row=1, column=1, padx=5, pady=5)

        tk.Label(root, text="Password:").grid(row=2, column=0, padx=5, pady=5)
        pass_entry = tk.Entry(root,show="*")
        pass_entry.grid(row=2, column=1, padx=5, pady=5)

        # Create a button to submit the data
        submit_button = tk.Button(root, text="Submit", command=lambda: submit_data(option_entry,username_entry,
        pass_entry))
        submit_button.grid(row=3, columnspan=2)
        
        #action=input("Please select options:\n1.Audit\n2.Extract transactions\n")
        '''if action=='1':
            renters=read_renters(work_folder+"\\"+renters_file)
            json_data=read_jsons(work_folder)
            result=audit_renters(renters,json_data)
            print_audit(renters,result)
        elif action=='2':
            query_transactins()'''
            
        root.mainloop()    

'''client = Client(timeout=10)
USERNAME=input("Username:")
PASSWORD=input("password:")
client.login(USERNAME, PASSWORD)
accounts=client.accounts()

accounk_link=client._accounts[-1].link
print("client._accounts:",client._accounts[-1].number,accounk_link)
result_url=change2first_date(accounk_link,'2024-03-24','2022-04-24')
#client.accounts()[-1].link=result_url

            
print("result_url:",result_url)
client._accounts[-1].link=result_url
transactions=client.transactions(accounts[-1])
print(transactions[-1]['date'])

#print(client.accounts()[-1].number,client.accounts()[-1].link)
#transactions=client.transactions(accounts[-1])
#print(transactions)'''

main()
