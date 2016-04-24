import csv
import time
from bs4 import BeautifulSoup
from urllib import urlopen
from datetime import datetime
from time import gmtime, strftime
# datetime usage:
# strftime("%Y-%m-%d_%H:%M:%S") -> '2015-09-13_00:43:20'
# strftime("%Y-%m-%d_%I:%M%p") -> '2015-09-13_12:45AM



def saveHTML(fileName, BeautifulSoupObject):
    fout = open(fileName, "w+")
    fout.write(str(BeautifulSoupObject.html))
    fout.close()

def getProdLinksFromPage(url):
    html = urlopen(url)
    bsObj = BeautifulSoup(html)
    divTag = bsObj.findAll("div", {"class":"displayItemTitle"})
    prod_links = []
    for entry in divTag:
        aTag = entry.find("a")
        if 'href' in aTag.attrs:
            #prodName = aTag.contents[0]
            prodURL = aTag.attrs['href']
            prod_links = prod_links + [prodURL]
            #print prodName, prodURL
    return prod_links


def getTable(trows):
    spec = dict()
    for row in trows:
        k = getContent(row.contents[0])
        v = getContent(row.contents[1])
        spec[k] = v
    return spec

def getContent(tag):
    return tag.get_text().encode('ascii').strip()


def pullPrice(tag):

    try:
        initPrice = getContent(tag.find("", {"class":"initialPriceTxt"}))
        siPrice = getContent(tag.find("", {"class":"siPriceTxt"}))
        return siPrice

    except:
        return getContent(tag.b) # <b>$99</b>


def getSpecFromProdPage(url):
    html = urlopen(url)
    bsObj = BeautifulSoup(html)

    # Get to the HTML table holding specification info
    div_id_storeItemSpecifications = bsObj.findAll("div", {"id":"storeItemSpecifications"})
    trows = div_id_storeItemSpecifications[0].findAll("tr")
    spec = getTable(trows) # Specifications given in tab table

    # Get Price
    td_class_discountRow = bsObj.find("td", {"class":"discountRow"})
    price = pullPrice(td_class_discountRow)
    spec['Price'] = price

    return spec

def saveToCSV(fileName, list_of_dictioanry, header=''):
    if header == '':
        header = list_of_dictioanry[0].keys()
    #header = list_of_dictionary[0].keys()
    with open(fileName, 'wb') as f:
        w = csv.DictWriter(f, header)
        w.writeheader()
        w.writerows(list_of_dictioanry)

def crawlProductLinks(prodLinks, time_delay):
    i = 1
    specList = []
    for link in prodLinks:
        spec = getSpecFromProdPage(link)
        spec['Product Link'] = link
        specList = specList + [spec]
        print i,'- Internal SKU ID:',spec['Internal SKU ID'], ' Price:', spec['Price'], ' Product Link:',spec['Product Link']
        i+=1
        time.sleep(time_delay)
        
    return specList

def build_header(dictionary):
    s = set()
    for d in dictionary:
        s = s.union(d.keys())
    return sorted(s)
    
    
def getPages(url_prodPage):
    numToDisplay = 100
    html = urlopen(url_prodPage)
    bsObj = BeautifulSoup(html)
    link = [url_prodPage] # this is the current page 1 - don't discount it!



    # Extract total number of products
    div_id_endecaSummary = bsObj.find("div", {"id":"endecaSummary"})
    nItems = int(getContent(div_id_endecaSummary).split()[0])

    # Build next pages
    if nItems > numToDisplay:
        
        # Go to the unordered list that tabulate next pages of products and get their "<a href=...></a>" tags
        ul_class_endecaPagination = bsObj.find("ul", {"class":"endecaPagination"})
        li_list = ul_class_endecaPagination.findAll("a") # could be None if only single page

        baseLink = li_list[0].attrs['href'].split('offset')[0]
        counter = numToDisplay
        while counter < nItems:
            link = link + [baseLink+'offset='+str(counter)]
            counter = counter + numToDisplay
    else:
        pass




    return link

def askUserInput():

    # URL
    url = raw_input('Enter a Product Listing url from Dellrefurbished.com: ')

    # Time delay
    while True:
        try:
            time_delay = raw_input('Time delay between crawling page (seconds)?: ')
            if time_delay == '':
                time_delay = 0
            return url, int(time_delay)
        except:
            print 'Time must be an integer. Try again.'


def collectProdLinks(pageLinks):
    # Gather all product links for all pages
    print ''
    prodLinks = []
    for link in pageLinks:
        print "Gathering page info: ", link
        linksFromCurrentPage = getProdLinksFromPage(link)
        prodLinks += linksFromCurrentPage
        print len(linksFromCurrentPage),"products found from this page."
    return prodLinks


def output_to_database():
    pass

### Testing
##url = "http://dellrefurbished.com/browse/?navDesc=16354+4294961203&sortby=P_discountPrice&hits=100"
##html = urlopen(url)
##bsObj = BeautifulSoup(html)
##
##
##link = getPages(url)
##print link
##print "Completed. Peaceful exit."

def loadSetting():
    configFile = "setting.txt"
    time_delay = ''
    list_of_labelAndURL = []

    fin = open(configFile, 'r')
    for line in fin:

        # Commented out line
        if (line[0] == '#') or line==('\n'):
            pass
        else:
            l = line.rstrip().split(',')

            # Parse time delay
            if l[0] == 'delay'.lower():
                while True:
                    try:
                        time_delay = int(l[1])
                        break
                    except:
                        print 'Time delay must be an integer'


            # Parse urls
            else:
                label = l[0]
                if label == '':
                    label = 'NoLabel'
                listing_url = l[1]
                list_of_labelAndURL += [ (label, listing_url) ]

    return time_delay, list_of_labelAndURL


def crawl_a_listing_url(time_delay, label, listing_url):

    # Some listing_url has more than 1 page (i.e. more than 100 listing per page), collect all pages.
    pageLinks = getPages(listing_url)

    # Given a listing url, extract all product page associated with each product listed
    listOfProdLinks = collectProdLinks(pageLinks)

    # Logistics print out
    n = len(listOfProdLinks)
    print "Total links found: ", n
    t = float(time_delay*n)
    if t < 60:
        print "Estimate time to completeion:", int(time_delay*n),"seconds."
    elif t < 60*60:
        print "Estimate time to completeion:", int(time_delay*n)/(60.0),"minutes."
    else:
        print "Estimate time to completeion:", float(time_delay*n)/(60.0*60.0),"hours."

    # Given a listing of product links, crwal through each one, and scrape specs of each product
    specList = crawlProductLinks(listOfProdLinks, time_delay)

    # Saving to files for now. Try database next.
    header = build_header(specList)
    fileName = label+"_"+strftime("%Y-%m-%d_%I.%M.%S_%p")+'.csv'
    saveToCSV(fileName, specList, header)
    print "Output saved to "+fileName+"."
    print "Completed. Peaceful exit."    



def main():

    # Load Setting file
    time_delay, list_of_labelAndURL = loadSetting()
    print 'Settings loaded:'
    print 'Time delay:', time_delay
    print 'Listings to crawl:'
    for label, listing_url in list_of_labelAndURL:
        print label, listing_url


    # Crawl through each labaled listing-url
    print ''
    for label, listing_url, in list_of_labelAndURL:
        print 'Crawling Now:', label
        crawl_a_listing_url(time_delay, label, listing_url)





if __name__ == "__main__":
    main()
    print 'End of program'
    pass











