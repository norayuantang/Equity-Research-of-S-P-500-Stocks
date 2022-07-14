# Project Option 2. Equity Research of S&P 500 Stocks
# User Interface:
# 1. The user can choose a company from a list of stocks in S&P 500 index
# Based on the choice of the company:
# 2. Your code calculates the short-term cost of capital (weighted-average of book debt and market equity)
#    Cost of equity uses the risk-free rate (3%), market return (10%) and the company's BETA
#    Cost of debt uses the ratio of interest expense and total debt (both long-term and short-term debts)
#    Weighs in WACC is based on the total book value of debt and total market equity (market cap)
# 3. You code calculates the short-term growth rate which is the higher number of two growth rates: Revenue growth rate and Earnings growth rate in the past four years
#    If both numbers are negative, then use 3% instead
# 4. Long-term cost of capital is the average of the short-term cost of capital of all firms in the same industry
# 5. Long-term growth rate is the average of the short-term growth rate of all firms in the same industry
# 6. Your code calculates the equity value per share using a two-stage model with a 10-year high growth period and a terminal value for low-growth period
# 7. If the equity value calculated is below market price, your code also suggests an alternative stock in the same industry of your choice, but it has a higher valuation relative to the market stock price


import random as rd
import pandas as pd
import numpy as np
import yfinance as yf
import datetime as dt
import tkinter as tk
import matplotlib.figure as fig
import matplotlib.backends.backend_tkagg as bac

def DownloadData(ticker, begin_day, end_day):
    try:
        dt.datetime.strptime(begin_day, '%Y-%m-%d')
        dt.datetime.strptime(end_day, '%Y-%m-%d')
        mydata = yf.download(ticker, begin_day, end_day)
        return mydata['Adj Close']
    except:
        print('Date must be entered as YYYY-MM-DD')

   
# Load all U.S. stocks in all sectors:
stock_list = pd.read_csv('sp500.csv')
tickers = stock_list['Ticker']
industries = stock_list['Industry']
founded = stock_list['Founded']

current_year = 2020
high_g_years = 10



#2 short-term cost of capital high cc
def wacc(ticker): 
    #short term cost of equity
    risk_free = 0.03
    market_ret = 0.1
    beta = fin_data.get_info()['beta']
    cost_equity = risk_free + beta * (market_ret - risk_free)
    
    #short term cost of debt
    int_exp = -income_stmt.loc['Interest Expense'][0]
    total_debt = balance_sheet.loc['Long Term Debt'][0] + balance_sheet.loc['Accounts Payable'][0] 
    cost_debt = int_exp / total_debt
    print(cost_debt)
    
    shares = fin_data.get_info()['sharesOutstanding']
    mydata = yf.download(ticker)
    price_data = mydata['Adj Close']
    mkt_cap = shares * price_data
    print(mkt_cap)
    #total book value of debt
    book_debt = balance_sheet.loc['Total Current Liabilities'][0] + balance_sheet.loc['Long Term Debt'][0]
    ev = mkt_cap + book_debt
    wacc = mkt_cap / ev * cost_equity + book_debt / ev * cost_debt 
    return wacc


#3 short-term growth rate 
def high_g(ticker):
    revenues = income_stmt.loc['Total Revenue']
    print(revenues)
    reversed_revenues = revenues.iloc[::-1]#倒转整个表
    revenue_growth = reversed_revenues / reversed_revenues.shift(1) - 1
    revenue_g = revenue_growth.mean()
    
    earnings = income_stmt.loc['Ebit']
    reversed_e = earnings.iloc[::-1]#倒转整个表
    e_growth = reversed_e / reversed_e.shift(1) - 1
    e_g = e_growth.mean()
    
    if revenue_g and e_g < 0 :
        high_g = 0.03
    else:
        high_g = max(revenue_g, e_g)
        
    return high_g

#4 long-term cost of capital lowcc
#5 long-term growth rate
industry = industries.loc['my_ticker']
sameind_tickers = tickers.loc[industry]
sameind_high_cc = []
sameind_high_g = []
for i in sameind_tickers:
    sameind_high_cc.append(wacc(i))
    sameind_high_g.append(high_g(i))
low_cc = np.mean(sameind_high_cc)
low_g = np.mean(sameind_high_g)


#6 ev pre share
def ev(ticker, current_year, high_g_years, high_g, wacc, low_g, low_cc):
    fin_data = yf.Ticker(ticker)
    tax_rate = 0.21
    terminal_year = current_year + high_g_years
    shares = fin_data.get_info()['sharesOutstanding']
    cash = balance_sheet.loc['Cash'][0]
    debt = balance_sheet.loc['Long Term Debt'][0]
    opt_cf = cash_flow.loc['Total Cash From Operating Activities'][0]
    int_exp = -income_stmt.loc['Interest Expense'][0]
    tax_shield = - int_exp * tax_rate
    cap_ex = cash_flow.loc['Capital Expenditures'][0]

    my_index = ['Period', 'Opt CF', 'Int Exp', 'Tax Shield', 'CapEx', 'CF', 'TV', 'FCF']
    my_data = np.array([0, opt_cf, int_exp, tax_shield, cap_ex, 0, 0, 0])
    my_series = pd.Series(my_data, name=current_year, index=my_index)
    my_df = pd.DataFrame(my_series)
    
    
    # high growth period
    for year in range(current_year+1, terminal_year+1):
        my_data = my_data * (1 + high_g)
        my_series = pd.Series(my_data, name=year, index=my_index)
        my_series.loc['Period'] = year - current_year
        my_df = pd.concat([my_df, my_series], axis=1)

    # low growth
    my_df.loc['CF'] = my_df.loc[['Opt CF', 'Int Exp', 'Tax Shield', 'CapEx']].sum()
    my_df.loc['TV', terminal_year] = my_df.loc['CF', terminal_year+1] / (low_cc - low_g)
    my_df.loc['FCF'] = my_df.loc['CF'] + my_df.loc['TV']
    my_df = my_df.drop(columns=[current_year, terminal_year])
    
    # PV = FCF/(1+r)^n
    my_df.loc['PV'] = my_df.loc['FCF'] / (1 + wacc) ** my_df.loc['Period']

    ev = my_df.loc['PV'].sum()
    price = (ev - debt + cash) / shares
    return price


#7 market price
def current_price(ticker):
    ticker = yf.Ticker(ticker)
    todays_data = ticker.history(period='1d')
    return todays_data['Close'][0]







#screen
mywindow = tk.Tk()
mywindow.geometry('500x800')
mywindow.title('Plotting in Tkinter')
tk.Label(mywindow, text = 'Ticker').pack(side=tk.TOP)
my_ticker_entry = tk.StringVar()
my_ticker = my_ticker_entry.get()

def PlotChart():
    try:
        data = DownloadData(my_ticker,my_begin.get(),my_end.get())
    except:
        print('Date must be entered as YYYY-MM-DD')
    myfig = fig.Figure(figsize = (4,3))
    myplot = myfig.add_subplot()
    myplot.plot(data, color='red')
    myplot.tick_params(axis='x', rotation=15)
    myplot.legend(loc='upper left')
    mycanvas = bac.FigureCanvasTkAgg(myfig, mywindow)
    mycanvas.get_tk_widget().place(x=650, y=125)

def Detail():
    my_industry.set(industry)
    my_mv.set(mkt_price)
    
def Search():
    ticker = my_ticker_entry.get()
    industry = stock_list.loc[my_ticker,'Industry']
    company = stock_list.loc[my_ticker,'Company']
    my_company.set(company)
    
def Recommendation():
    my_recommendation.set(better_stock)
    
def Valuation():
    my_estimation.set(esti_price)
    
def ExitNow():
    mywindow.destroy()


my_ticker_entry = tk.StringVar()
ticker = my_ticker_entry.get()
fin_data = yf.Ticker(ticker) 
income_stmt = fin_data.get_financials()
balance_sheet = fin_data.get_balancesheet()
cash_flow = fin_data.get_cashflow()

#recommandation
esti_price = ev(ticker, current_year, high_g_years, high_g, wacc, low_g, low_cc)
if esti_price < current_price(ticker):
        better_stock = []
        for i in sameind_tickers:
            esti_price_else = ev(i)
            mkt_price = current_price(i)
            if esti_price_else > mkt_price:
                better_stock.append(i)
        print('Better choice in the same industry: ', better_stock)


#create a window
mywindow = tk.Tk()
mywindow.geometry('500x800')
mywindow.title('Equity Research')
#create a frame inside the window
myframe = tk.Frame(mywindow)
myframe.place(x = 0,y = 100)
myscroll = tk.Scrollbar(myframe, orient = tk.VERTICAL)
myselect = tk.Listbox(myframe, yscrollcommand=myscroll.set)
myselect.pack(side=tk.LEFT)
myscroll.config(command=myselect.yview)
myscroll.pack (side=tk.RIGHT, fill=tk.Y)
#for i in tickers:
#    myselect.insert(tk.END, i)
#labels
tk.Label(mywindow, text = 'Ticker').place(x=0,y=50)
my_ticker_entry = tk.StringVar()
tk.Entry(mywindow,textvariable = my_ticker_entry).place(x=100,y=50)

tk.Label(mywindow, text = 'COMPANY').place(x=300,y=75)
my_company = tk.StringVar()
tk.Entry(mywindow,textvariable = my_company).place(x=400,y=75)

tk.Label(mywindow, text = 'INDUSTRY').place(x=300,y=125)
my_industry= tk.StringVar()
tk.Entry(mywindow,textvariable = my_industry).place(x=400,y=125)

tk.Label(mywindow, text = 'LAST MV').place(x=300,y=175)
my_mv = tk.StringVar()
tk.Entry(mywindow,textvariable = my_mv).place(x=400,y=175)

tk.Label(mywindow, text = 'ESTIMATION').place(x=300,y=225)
my_estimation = tk.StringVar()
tk.Entry(mywindow,textvariable = my_estimation).place(x=400,y=225)

tk.Label(mywindow, text = 'RECOMMEND').place(x=300,y=275)
my_recommendation = tk.StringVar()
tk.Entry(mywindow,textvariable = my_recommendation).place(x=400,y=275)

tk.Label(mywindow, text = 'BEGIN').place(x=300,y=325)
my_begin = tk.StringVar()
tk.Entry(mywindow,textvariable = my_begin).place(x=400,y=325)

tk.Label(mywindow, text = 'END').place(x=300,y=375)
my_end = tk.StringVar()
tk.Entry(mywindow,textvariable = my_end).place(x=300,y=375)

tk.Label(mywindow,text = 'yyyy-mm-dd').place(x=500,y=375)
tk.Label(mywindow,text = 'yyyy-mm-dd').place(x=500,y=425)


# All buttons for your choice
tk.Button(mywindow, text = 'SEARCH', command = Search).place(x=200, y=100)
tk.Button(mywindow, text = 'DETAIL', command = Detail).place(x=200, y=150)
tk.Button(mywindow, text = 'Valuation', command = Valuation).place(x=200, y=200)
tk.Button(mywindow, text = 'EXIT', command = ExitNow).place(x=200, y=250)
tk.Button(mywindow,text = 'PLOT', command = PlotChart).place (x = 600,y= 50)

mywindow.mainloop()





