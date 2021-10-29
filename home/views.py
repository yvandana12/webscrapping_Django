from django.shortcuts import render, HttpResponse


#for getting details of company from the UK House number website
def get_data_from_uk(houseno):
  """
  Description: This function is designed to get company information from uk website
  Input: This function takes company house number as input,
  Output: This functions returns the extracted information from uk website
  """

  #getting imports
  import requests
  from bs4 import BeautifulSoup
  import datefinder

  #url to get information from uk website
  url_uk='https://find-and-update.company-information.service.gov.uk/company/0'+houseno
   
  r=requests.get(url_uk)
  r.headers['Content-type']
  htmlContent=r.content

  #BeautifulSoup parses the data using HTML parser or any other.
  soup=BeautifulSoup(htmlContent,'html5lib')

  #getting company name
  companyname=soup.find('p',class_='heading-xlarge').text

  #getting company number
  companynum=soup.find('p',id='company-number').text

  #getting company status and account status
  companystatus=soup.find('dd',class_='text data', id='company-status').text
  accountstatus=soup.find_all('p')[9]
  accountstatus=accountstatus.get_text().strip()
  matches = list(datefinder.find_dates(accountstatus))
  if(matches):
    accountstatus="Accounts Filed"
  else:
    accountstatus="Accounts Not Filed"

  #getting industry details
  industry=soup.find('span',id='sic0').text
  industry=industry[industry.find('-')+1:]
    
  #return extracted details
  return companyname, companynum,companystatus, accountstatus,industry

#storing json file of company 1 to mongoDB
def mongodb_store():
  import pymongo
  from pymongo import MongoClient
  import json
  client=MongoClient('mongodb://127.0.0.1:27017')
  db=client['companies_data']
  collection=db['contract_engineers']
  with open('company_1.json') as file:
    file_data=json.load(file)
  collection.insert_many(file_data)

#storing json file company 2 to mongoDB
def mongodb_store2():
  import pymongo
  from pymongo import MongoClient
  import json
  client=MongoClient('mongodb://127.0.0.1:27017')
  db=client['companies_data']
  collection=db['FSG_tools_and_die']
  with open('company_2.json') as file:
    file_data=json.load(file)
  collection.insert_many(file_data)


#get html data of company 1 through this function
def get_html_content(company_url):

  """"
  Description: This method is designed to scrap the data from company url and return meaningful data as dictionary
  Input: This function recieves company url as input
  Output: This function returns data scrapped from comapny url recieved as input
  """
  try:
    import requests
    from bs4 import BeautifulSoup
    import pandas as pd
    import re
    from unicodedata import normalize

    url=company_url

    r=requests.get(url)
    r.headers['Content-type']
    htmlContent=r.content

    soup=BeautifulSoup(htmlContent,'html5lib')

    #extract summary from main page
    summary=''
    count=0
    for paras in soup.find_all('p',class_='font_7'):
      count+=1
      if(count<6):
        summary+=paras.get_text()

    summary=summary.replace('\xa0', ' ').rstrip()
    summary=summary.replace('\u200b', ' ').rstrip()
    summary=summary.replace('\n', ' ').rstrip()
    summary=summary.replace('\u200b', ' ').rstrip()
    summary=summary.replace('-', ' ').rstrip()
    
    #getting quality certification details from summary extracted
    match=re.findall('\d{4}:\d{4}',summary)
    quality_cert=str(match[0])

    #get company home number
    companyhousenumber=''
    for i in soup.find_all('div',id='comp-kc0cbq8g',class_='_1Q9if'):
      for paras in i.find('p',class_='font_8'):
          companyhousenumber+=paras.get_text()
    companyhousenumber=companyhousenumber[companyhousenumber.index('.')+1:].split('\n')[0]
      
    #after getting comapany house number get information about company from uk house number website
    details_from_uk=get_data_from_uk(companyhousenumber)

    #details of comapny from uk website
    companyname=details_from_uk[0].strip()
    companyhousenumber=details_from_uk[1].strip()
    res = [int(i) for i in companyhousenumber.split() if i.isdigit()]
    companyhousenumber=res
      
    companystatus=details_from_uk[2].strip()
    accountstatus=details_from_uk[3]
    industry=details_from_uk[4].strip()

    #get products from drop down list 
    products=''
    for i in soup.find_all('li',id='comp-igauz7ee0'):
      for j in i.find_all('li'):
        products+=j.text+" , "
              

    #get services from the drop down list
    services=''
    for i in soup.find_all('li',id='comp-igauz7ee1'):
      for j in i.find_all('li'):
        services+=j.text+" , "


    #get recent news links for the company    
    url2=url+'/news'  #changes url as news is in diffrent page
    r1=requests.get(url2)
    r1.headers['Content-type']
    htmlContent1=r1.content
    recentnews=''
    soup1=BeautifulSoup(htmlContent1,'html5lib')
    recentnews=''
    for article in soup1.find_all('article', class_='_3q7Xn'):
      for news in article.find_all('a'):
        if(news.get('href')!=None):
          recentnews+=news.get('href')
          recentnews+="     "

    socialhandle=''
    for i in soup.find('div',class_='_1_UPn'):
      count=0
      for j in i.find_all('a'):
        count+=1
        socialhandle+=j.get('href')+" "
        if(count==2):
          break

    #get about page information 
    url3=url+'/about'  #changes url as news is in diffrent page
    r2=requests.get(url3)
    r2.headers['Content-type']
    htmlContent2=r2.content
    soup2=BeautifulSoup(htmlContent2,'html5lib')
    detailedabout=''
    for i in soup2.find_all('p',class_='font_8'):
      detailedabout+=i.get_text().strip()
    detailedabout=detailedabout.replace('\u200b', ' ').rstrip() 
    

    #form dictionary from all the details extarcted
    dict={
          'name':companyname,
          'summary':summary,
          'companyhousenumber':companyhousenumber,
          'companystatus':companystatus,
          'companyfinancialstatus':accountstatus,
          'url':url,
          'typesofproducts':products,
          'typesofservices':services,
          'industry':industry,
          'recentnews':recentnews,
          'socialhandles':socialhandle,
          'qualitycertifications':quality_cert,
          'detailedabout':detailedabout
    }

    df = pd.DataFrame(dict) 
    df.to_json("company_1.json", orient="records")
    #mongodb_store()
    return dict
  except:
    return "Error Occured!"

#get html data of company 2 through this function
def get_html_content2(company_url):

  """"
  Description: This method is designed to scrap the data from company url and return meaningful data as dictionary
  Input: This function recieves company url as input
  Output: This function returns data scrapped from comapny url recieved as input
  """
  #I will use Beautifulsoup form scrapping html data from url
  
  try:
    import requests
    from bs4 import BeautifulSoup
    import pandas as pd
    import re
    from unicodedata import normalize

    url=company_url
    r=requests.get(url)
    r.headers['Content-type']
    htmlContent=r.content

    #BeautifulSoup parses the data using HTML parser or any other.
    soup=BeautifulSoup(htmlContent,'html5lib')
    
    #Extracting summary from soup and removing unwanted characters
    summary=''
    summary=soup.find_all('div',class_='col-xs-12')[1]
    summary=summary.find('p').get_text()
    summary1=soup.find_all('div',class_='card-text')
    for i in summary1:
      summary=summary+i.get_text().strip()
    summary=summary.replace('\u2013'," ")

    #Get information about company from uk house number website
    details_from_uk=get_data_from_uk('0680756')

    #details of comapny from uk website
    companyname=details_from_uk[0].strip()
    companyhousenumber=details_from_uk[1].strip()
    res = [int(i) for i in companyhousenumber.split() if i.isdigit()]
    companyhousenumber=res
    companystatus=details_from_uk[2].strip()
    accountstatus=details_from_uk[3]
    industry=details_from_uk[4].strip()

    
    #get products from drop down list 
    products=""
    for j in soup.find_all('a',class_='parent'):
      products+=j.text+" , "

    #get services from the drop down list
    services=""
    for i in soup.find_all('li',class_='menu-level-2'):
      services+=i.find('a').get_text()+" , "

    #get recent news links for the company    
    url2=url+'/news'  #changes url as news is in diffrent page
    r1=requests.get(url2)
    r1.headers['Content-type']
    htmlContent1=r1.content
    soup1=BeautifulSoup(htmlContent1,'html5lib')
    recentnews=''
    for article in soup1.find_all('div', class_='news-article-item'):
      for news in article.find_all('a'):
        if(news.get('href')!=None):
          recentnews+=url+news.get('href')
          recentnews+=" \n"

    #we could not get quality certification details
    quality_cert=""

    #get about page information 
    url3=url+'/about-us'  #changes url by adding about in url about is in diffrent page
    r2=requests.get(url3)
    r2.headers['Content-type']
    htmlContent2=r2.content
    detailedabout=''
    count=1

    #now we can get data from about page of company website
    soup2=BeautifulSoup(htmlContent2,'html5lib')

    #getting all the text from about page
    for para in soup2.find_all('p'):
      if(count<7):
        detailedabout+=para.get_text()
      count+=1
    #removing unwanted charcters
    detailedabout=detailedabout.replace('\xa0', ' ').rstrip() 
    detailedabout=detailedabout.replace('-', ' ').rstrip() 
    detailedabout=detailedabout.replace('\u2013', ' ').rstrip() 

    #getting links of social handles of the company
    socialhandle=''
    socialhandle=soup.find('span',class_='social-icon').find('a')
    socialhandle=socialhandle.get('href')

    #form dictionary from all the details extarcted
    dict={
          'name':companyname,
          'summary':summary,
          'companyhousenumber':companyhousenumber,
          'companystatus':companystatus,
          'companyfinancialstatus':accountstatus,
          'url':url,
          'typesofproducts':products,
          'typesofservices':services,
          'industry':industry,
          'recentnews':recentnews,
          'socialhandles':socialhandle,
          'qualitycertifications':quality_cert,
          'detailedabout':detailedabout
    }

    #now writting data to a jsonfile
    df = pd.DataFrame(dict) 
    df.to_json("company_2.json", orient="records")

    #storing data to database MongoDB
    #mongodb_store2()

    #returning dictionary 
    return dict
  
  except:
    return "Error Occured!"

# To render data into a pdf and dynamically downoad the pdf
def render_pdf_view(request,data):
    from xhtml2pdf import pisa
    from django.template.loader import get_template
    #print("here")
    template_path='pdf.html'
    context=data
    response=HttpResponse(content_type='application/pdf')
    response['Content-Disposition']='attachment; filename="report1.pdf"'

    template=get_template(template_path)
    #print(context)
    html=template.render(context)
    #print(html)
    pisa_status=pisa.CreatePDF(html,dest=response)

    if pisa_status.err:
        return HttpResponse('We had some error ')
    print(response)
    return response

#to generate answers from the data scrapped using Huggingface interface API 
def get_answers(company_url):
  """
  Description: This function is designed to answer the questions with context of scrapped data,
    generate a report based on the answers to the question and scrapped data both.
  Input: This function takes company url as input
  Output: A pdf with complete report will be generated (named : company_2_report)

  """
  url=company_url

  if(url=="https://www.contractsengineering.com"):
  #getting all the data as dictionary object
    dict=get_html_content(url)
  else:
    dict=get_html_content2(url)

  if( dict == "Error Occured!"):
    return dict

  #now form a paragraph from all the scrapped data in a variable named context 
  #this context variable will be passes as Context for answering the questions
  Context=""
  for i in dict.values():
    if type(i)!=list:
      Context+=i+" "

  
  #performing api call to get answers to our quesions from the contxt pepared context
  import json
  import requests

  #this api token
  API_TOKEN="api_XkRolPMhAWhANLryjMDRJJXWPOJpmaZARO"

  headers = {"Authorization": f"Bearer {API_TOKEN}"}
  API_URL = "https://api-inference.huggingface.co/models/deepset/bert-base-cased-squad2"

  def query(payload):
	  response = requests.post(API_URL, headers=headers, json=payload)
	  return response.json()

  #querying from the api
  answer1 = query(
      {
          "inputs": {
              "question": "What the company does?",
              "context": Context,
          }
      }
  )
  
  answer2 = query(
      {
          "inputs": {
              "question": "Which Industry is the company in?",
              "context": Context,
          }
      }
  )
  
  answer3 = query(
      {
          "inputs": {
              "question": "What are the products or services, the company offers?",
              "context": Context,
          }
      }
  )

  answer4 = query(
      {
          "inputs": {
              "question": "What Quality Certifications it has?",
              "context": Context,
          }
      }
  )
  
  answer5 = query(
      {
          "inputs": {
              "question": "Where are its products supplied and who are its customers?",
              "context": Context,
          }
      }
  )
  data = {
        "CompanyName": dict['name'],
        "Summary": dict['summary'],
        "CompanyHouseNumber": str(dict['companyhousenumber']),
        "CompanyStatus":dict['companystatus'],
        "CompanyFinancialStatus": dict['companyfinancialstatus'],
        "Url": dict['url'],
        "TypesofProducts": dict['typesofproducts'],
        "TypesofServices": dict['typesofservices'],
        "Industry":answer1['answer'],
        "RecentNews": dict['recentnews'],
        "SocialMediaHandle" : dict['socialhandles'],
        "QualityCertifications": answer4['answer'],
        "Customers": answer5['answer'],
  }

  return data
  
#view of the page
def index(request):

  if 'company' in request.GET:
    #fetch website data
    company_url=request.GET.get('company')
    print(company_url)
    data=get_answers(company_url)
    if(data=="Error Occured!"):
      print(data)#print error
      return render(request,'index.html')#render index.html again
    else:
      return render_pdf_view(request,data)
      #return render(request,'index.html')
  else:
    return render(request,'index.html')
