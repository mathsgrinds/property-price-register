import mechanize
import os
import csv
import random
import time
from bs4 import BeautifulSoup
import unicodedata
import re
import urllib2

# Set this to "False" for faster downloading but of course without eircodes in the address
witheircodes = True

useragent = "Mozilla/5.0 (Windows NT 10.0; WOW64; rv:49.0) Gecko/20100101 Firefox/49.0"
entry = ''
browser = mechanize.Browser(factory=mechanize.RobustFactory())
url = "https://www.propertypriceregister.ie/website/npsra/pprweb.nsf/PPR?OpenForm"
browser.addheaders = [('User-agent',useragent)]
browser.open(url)
browser.select_form(nr=0)
AllCounties = browser.possible_items("County")
AllYears = browser.possible_items("Year")
AllCounties = [x for x in AllCounties if x]
AllYears = [x for x in AllYears if x]
AllYears.reverse()
global filename
filename = "propertypriceregister.csv"
if not os.path.exists(filename):
    if witheircodes:
        header = '"Date","Price","Url","Address","Eircode","County"'+"\n"
    else:
        header = '"Date","Price","Url","Address","County"'+"\n"        
    with open(filename, 'a') as f:
        f.write(header)

def eircode(address):
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
    soup = BeautifulSoup(html, "html.parser")
    tag = soup.find(id="ctl00_body_hfTextToCopy")
    try:
        value = tag['value']
        address = value.replace("\n",", ")
        return str(address.split(",")[-1].strip(" "))
    except:
        return "NA" # Known Issue: Searching for addresses in Irish on An Post often fails -- odd

for year in AllYears:
    for county in AllCounties:
        browser.open(url)
        browser.select_form(nr=0)
        browser["Year"] = [year]
        browser["County"] = [county]
        browser["StartMonth"] = ["01"]
        browser["EndMonth"] = ["12"]
        browser.submit()
        print "Searching: "+county+", "+year
        html = browser.response().read()
        soup = BeautifulSoup(html, "html.parser")
        results = soup.find("table", {"class" : "resultsTable"})
        for row in results.findAll("tr"):
            for col in row.findAll("td"):
                try:
                    contents = col.contents[0]
                    smallsoup = BeautifulSoup(contents, "html.parser")
                    entry += '"'+contents.replace("\n","")+'",'
                except:
                    contents = str(col.contents[0])
                    smallsoup = BeautifulSoup(contents, "html.parser")
                    link = smallsoup.find("a")
                    entry += '"'+"https://www.propertypriceregister.ie/Website/npsra/PPR/npsra-ppr.nsf/"+link["href"].replace("\n","")+'",'
                    if witheircodes:
                        entry += '"'+link.contents[0].replace("\n","")+'","'+eircode(link.contents[0].replace("\n",""))+'","'+county+'"\n'
                    else:
                        entry += '"'+link.contents[0].replace("\n","")+'","'+county+'"\n'                        
                    entry = str(unicodedata.normalize('NFKD', entry).encode('ascii','ignore'))
            if witheircodes:
                with open(filename,'a') as f: f.write(entry)
                entry = ''
        if not witheircodes:
            with open(filename,'a') as f: f.write(entry)
            entry = ''
quit()