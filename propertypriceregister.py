import mechanize
import os
import csv
import random
import time
from bs4 import BeautifulSoup
import unicodedata
import re
import urllib2

global AllCounties
global AllYears

mechanize._sockettimeout._GLOBAL_DEFAULT_TIMEOUT = 100
url = "https://www.propertypriceregister.ie/website/npsra/pprweb.nsf/PPR?OpenForm"
useragent = "Mozilla/5.0 (Windows NT 10.0; WOW64; rv:49.0) Gecko/20100101 Firefox/49.0"
browser = mechanize.Browser(factory=mechanize.RobustFactory())
browser.addheaders = [('User-agent',useragent)]
browser.open(url)
browser.select_form(nr=0)
AllCounties = browser.possible_items("County")
AllCounties = [x for x in AllCounties if x]
AllYears = browser.possible_items("Year")
AllYears = [x for x in AllYears if x]

def routingkey(address):
    useragent = "Mozilla/5.0 (Windows NT 10.0; WOW64; rv:49.0) Gecko/20100101 Firefox/49.0"
    browser = mechanize.Browser(factory=mechanize.RobustFactory())
    url = "http://correctaddress.anpost.ie/pages/Search.aspx"
    browser.addheaders = [('User-agent', useragent)]
    browser.open(url)
    html = browser.response().read()
    browser.select_form(nr=0)
    browser.form.set_all_readonly(False)
    browser["ctl00$body$txtAutoComplete"] = str(address)
    request = browser.form.click()
    response = browser.submit()
    html = response.read()
    routingkey = "NA"
    for x in re.findall("[A-Z][0-9][0-9]\s[A-Z0-9][A-Z0-9][A-Z0-9][A-Z0-9]", html):
        routingkey = x.split(" ")[0]
    return routingkey

def New(url):
    useragent = "Mozilla/5.0 (Windows NT 10.0; WOW64; rv:49.0) Gecko/20100101 Firefox/49.0"
    browser.addheaders = [('User-agent',useragent)]
    browser.open(url)
    html = browser.response().read()
    if "New Dwelling" in html:
        return "TRUE"
    else:
        return "FALSE"
    
def worker(year):
    for county in AllCounties:
        while True:
            try:
                print "Downloading: "+county
                useragent = "Mozilla/5.0 (Windows NT 10.0; WOW64; rv:49.0) Gecko/20100101 Firefox/49.0"
                url = "https://www.propertypriceregister.ie/website/npsra/pprweb.nsf/PPR?OpenForm"
                browser.addheaders = [('User-agent',useragent)]
                browser.open(url)
                browser.select_form(nr=0)
                browser["Year"] = [year]
                browser["County"] = [county]
                browser["StartMonth"] = ["01"]
                browser["EndMonth"] = ["12"]
                browser.submit()
                html = browser.response().read()
                soup = BeautifulSoup(html, "html.parser")
                results = soup.find("table", {"class" : "resultsTable"})
                break
            except:
                continue
        for row in (results.findAll("tr"))[2:]:
            while True:
                try:
                    r = str(row).split("</td>")
                    Date = re.sub('<[^>]*>', '', r[0])
                    Price = re.sub('<[^>]*>', '', r[1])
                    Price = Price[3:].replace(",","")
                    for x in re.findall("href=\".*\"\s", r[2]):
                        NewDwelling = New("https://www.propertypriceregister.ie/website/npsra/PPR/npsra-ppr.nsf/"+x.replace('href="','').replace('"',''))
                    if " **" in Price:
                        FullMarketPrice = "FALSE"
                    else:
                        FullMarketPrice = "TRUE"
                    Price = Price.replace(" **","")
                    Address = re.sub('<[^>]*>', '', r[2]).upper()
                    RoutingKey = routingkey(Address)
                    entry =  '"'+Date+'","'+Price+'","'+Address+'","'+FullMarketPrice+'","'+county+'","'+RoutingKey+'","'+NewDwelling+'"'+"\n"
                    if not os.path.exists(year+".csv"):
                        header = '"Date","Price","Address","FullMarketPrice","County","RoutingKey","NewDwelling"'+"\n"      
                        with open(year+".csv", 'a') as f:
                            f.write(header)
                    with open(year+".csv",'a') as f: f.write(entry)
                    break
                except:
                    continue

for year in AllYears:
    worker(year)

quit()
