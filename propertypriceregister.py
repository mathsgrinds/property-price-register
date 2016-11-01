import mechanize
import os
import csv
import random
import time
from bs4 import BeautifulSoup
import unicodedata
import re
import urllib2
import threading

global AllCounties
global AllYears

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

data = [set() for i in range(len(AllYears))]
for year in AllYears:
    j = int(year)-int(min(AllYears))
    data[j] = set()
    try:
        with open(year+'.csv', 'rb') as f:
            reader = csv.reader(f)
            for row in reader:
                data[j].add(str(row[0]))
    except:
        pass

def GetRoutingKey(address):
    while True:
        try:
            print "Getting Routing Key for "+address
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
            if "no results" in html.lower():
                return "NA"
            elif "no results" not in html.lower():
                try:
                    key = (re.findall("[A-Z][0-9][W-W0-9]\s[A-Z0-9][A-Z0-9][A-Z0-9][A-Z0-9]", html))[0].split(" ")[0]
                    if key is not None:
                        return key
                except:
                    return "NA"
        except:
            pass

def DownloadRegister(year, county):
    while True:
        try:
            print "Downloading Register for "+county+", "+year
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
            if "no results" in html.lower():
                return "NA"
            elif "no results" not in html.lower():
                try:
                    soup = BeautifulSoup(html, "html.parser")
                except:
                    soup = BeautifulSoup(html)
                results = soup.find("table", {"class" : "resultsTable"})
                if results is not None:
                    return results
        except:
            pass

def GetSaleInfo(url):
    while True:
        try:
            print "Getting Sale Info from "+url
            useragent = "Mozilla/5.0 (Windows NT 10.0; WOW64; rv:49.0) Gecko/20100101 Firefox/49.0"
            browser = mechanize.Browser(factory=mechanize.RobustFactory())
            browser.addheaders = [('User-agent', useragent)]
            browser.open(url)
            html = browser.response().read()
            try:
                soup = BeautifulSoup(html, "html.parser")
            except:
                soup = BeautifulSoup(html)
            results1 = soup.find("table", {"id" : "SaleInfo"})
            results2 = soup.find("table", {"id" : "OtherInfo"})
            results = str(results1)+str(results2)
            if results is not None:
                return results
        except:
            pass

def SaveEntry(filename, entry):
    print "Saving to CSV file: "+entry.rstrip("\n")
    if not os.path.exists(filename+".csv"):
        with open(filename+".csv", 'a') as f:
            f.write('"Address","RoutingKey","Date","Price","FullMarketPrice","VATExclusive","DescriptionofProperty","PropertySizeDesc","OtherPropertiesInThisSale"'+"\n" )
    with open(filename+".csv",'a') as f: f.write(entry)
    print "-----------------------------------------------------------------------------------------------------------------------------------------------------------------------"

def worker(year):
    j = int(year)-int(min(AllYears))
    for county in AllCounties:
        results = DownloadRegister(year, county)
        if results != "NA":
            for result in (results.findAll("tr"))[2:]:
                r = str(result).split("</td>")
                Date = re.sub('<[^>]*>', '', r[0])
                url = "https://www.propertypriceregister.ie/website/npsra/PPR/npsra-ppr.nsf/" + r[2].split('"')[1]
                Price = (re.sub('<[^>]*>', '', r[1]))[3:].replace(",","")
                if " **" in Price:
                    FullMarketPrice = "FALSE"
                else:
                    FullMarketPrice = "TRUE"
                Price = Price.replace(" **","")
                Address = re.sub('<[^>]*>', '', r[2]).upper()
                if Address not in data[j]:
                    RoutingKey = GetRoutingKey(Address)
                    SaleInfo = GetSaleInfo(url)
                    VATExclusive = str(SaleInfo).split("<tr>")[4].split("<td>")[2].split("</td>")[0].strip("\n").strip(" ").replace("Yes","TRUE").replace("No","FALSE")
                    DescriptionofProperty = str(SaleInfo).split("<tr>")[5].split("<td>")[2].split("</td>")[0].strip("\n").strip(" ")
                    PropertySizeDesc =  str(SaleInfo).split("<tr>")[6].split("<td>")[2].split("</td>")[0].strip("\n").strip(" ")
                    OtherPropertiesInThisSale = str(SaleInfo).split("<tr>")[7].split("<td>")[1].split("</td>")[0].strip("\n").strip(" ")
                    entry =  ('"'+Address+'","'+RoutingKey+'","'+Date+'","'+Price+'","'+FullMarketPrice+'","'+VATExclusive+'","'+DescriptionofProperty+'","'+PropertySizeDesc+'","'+OtherPropertiesInThisSale+'"'+"\n").upper()
                    SaveEntry(year, entry)
                else:
                    try:
                        print "Skipping: "+Address.rstrip("\n")
                    except:
                        pass

threads = []
for i in AllYears:
    t = threading.Thread(target=worker, args=(i,))
    threads.append(t)
    t.start()
