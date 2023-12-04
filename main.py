import requests
from bs4 import BeautifulSoup
import pandas as pd
import re
import time

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

driver = webdriver.Chrome()



base_url = "https://www.104.com.tw/jobs/search/"
params = {
    'ro': 0,
    'jobcat': 2008000000,
    'expansionType': 'area,spec,com,job,wf,wktm',
    'area': 6002000000, # china
    'order': 17,
    'asc': 0,
    'mode': 'l',
    'jobsource': 'cmw_redirect',
    'langFlag': 0,
    'langStatus': 0,
    'recommendJob': 1,
    'hotJob': 1,
    'page': 1  # Start from the first page
}

# this is bad design. only allows diff searches baesd on locations.
china_param = "6002000000"
taiwan_param = "6001001000, 6001002000, 6001003000, 6001004000, 6001005000, 6001006000, 6001007000, 6001008000, 6001010000, 6001011000, 6001012000, 6001013000, 6001014000, 6001016000, 6001018000, 6001019000, 6001020000, 6001021000, 6001022000, 6001023000"
searches = [china_param, taiwan_param]

df = pd.DataFrame(columns=['job_name',
                           'job_url',
                           'location',
                           'area',
                           'company',
                           'education',
                           'experience',
                           'role_types'
                           'salary',
                           'shift_time',
                           'role_term',
                           'skills'
                           ])


for search in searches:
    # search for a particular area, get url for params
    params["area"] = search
    r = requests.get(base_url, params=params)
    initial_url = str(r.url)
    print(initial_url)

    # use selenium to dynamically load page and get page number
    driver.get(initial_url)
    # driver.implicitly_wait(3)
    wait = WebDriverWait(driver, 3)
    select_element = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "select.page-select.js-paging-select.gtm-paging-top")))

    # Find all option elements within the select tag
    options = select_element.find_elements(By.TAG_NAME, "option")

    # Get the value of the last option
    last_page = int(options[-1].get_attribute("value")) if options else None
    print(last_page)

    # make new search for each page
    for page in range(1,last_page+1):
        params["page"] = page 
        search_page = requests.get(base_url, params=params)
        search_soup = BeautifulSoup(search_page.content, "html.parser")
        jobs = search_soup.find_all(class_="job-mode js-job-item")
        for job in jobs:
            # job_name
            job_name = (job.find("a", class_="js-job-link")).text
            print(job_name)
            #job_url
            job_url = "http://" + (job.find("a", class_="js-job-link"))["href"][2:]
            print(job_url)
            # location
            # if url is china_url: location = "China"
            if params["area"] == "6002000000": location = "China"
            else: location = "Taiwan"
            print(location)
            # area
            area = (job.find("li", class_="job-mode__area")).text
            print(area)
            # company; use regex
            company = (job.find("a", {"title": re.compile(r"公司名")})).text
            print(company)
            # education
            education = (job.find("li", class_="job-mode__edu")).text
            print(education)
            # experience
            experience = (job.find("li", class_="job-mode__exp")).text
            print(experience)

            # enter job page for other info
            job_page = requests.get(job_url)
            job_soup = BeautifulSoup(job_page.content, "html.parser")
            # salary
            salary_label = job_soup.find(lambda tag: tag.name == "h3" and "工作待遇" in tag.text)
            if salary_label and salary_label.parent and salary_label.parent.find_next_sibling():
                salary = salary_label.parent.find_next_sibling().get_text(strip=True)
                print(salary)
            else:
                print("Element not found")
            # role_type
            role_types = [x.text for x in job_soup.find_all('u', attrs={'data-v-71fba476': True})]
            print(role_types)
            # shift_time (day, etc)
            # no unique identifier; must simply match with label and find sibling
            shift_label = job_soup.find(lambda tag: tag.name == "h3" and "上班時段" in tag.text)
            # Navigate to the sibling element and extract the text
            if shift_label and shift_label.parent and shift_label.parent.find_next_sibling():
                shift_time = shift_label.parent.find_next_sibling().get_text(strip=True)
                print(shift_time)
            else:
                print("Element not found")
            # role_term (full-time?)
            term_label = job_soup.find(lambda tag: tag.name == "h3" and "工作性質" in tag.text)
            if term_label and term_label.parent and term_label.parent.find_next_sibling():
                role_term = term_label.parent.find_next_sibling().get_text(strip=True)
                print(role_term)
            else:
                print("Element not found")
            # skills
            skills = [x.text for x in job_soup.find_all('u', attrs={'data-v-705729d0': True, 'data-v-1392b104': True})]
            print(skills)

            # add to dataframe
            row = {
                'job_name' : job_name,
                'job_url': job_url,
                'location': location,
                'area': area,
                'company': company,
                'education' : education,
                'experience': experience,
                'role_types': ','.join(role_types),
                'salary': salary,
                'shift_time': shift_time,
                'role_term': role_term,
                'skills': ','.join(skills)
            }
            print(row)
            row_df = pd.DataFrame([row])
            df = pd.concat([df, row_df], ignore_index = True)

        
df.to_csv('out.csv')



