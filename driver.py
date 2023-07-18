import sys
import json
import time
import csv
import traceback
from datetime import datetime

from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager 
from selenium.webdriver.common.by import By
from selectorlib import Extractor
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC


def get_urls_from_category(url: str, pages: int):
    """ Get all product urls from a given category and save to urls.txt """
    
    driver = webdriver.Chrome(service = Service(ChromeDriverManager().install()))
    
    driver.get(url)
    
    with open("urls.txt", "w") as outfile:
        for _ in range(1, pages+1):  
            print(f"Page: {_} / {pages}")

            # Get the links from driver
            h2_elements = driver.find_elements(By.CSS_SELECTOR, 'h2.a-size-mini.a-spacing-none.a-color-base.s-line-clamp-2')
            
            # Extract the href attribute of the a element within each h2 element
            links = [h2.find_element(By.TAG_NAME, "a").get_attribute('href') for h2 in h2_elements]

            for link in links:
                outfile.write(link)
                outfile.write("\n")

            if _ == pages:
                break

            # Click next page
            try:
                element = WebDriverWait(driver, 10).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, "a.s-pagination-item.s-pagination-next.s-pagination-button.s-pagination-separator"))
                )
                element.click()

                time.sleep(2)
                
            except Exception as e:
                print(f"Element not found: {e}")

    # Close the browser
    driver.quit()

def scrape_urls():

    e = Extractor.from_yaml_file('selectors.yml')
    
    total = 0
    count = 0
    skipped = 0

    driver = webdriver.Chrome(service = Service(ChromeDriverManager().install()))

    with open("urls.txt",'r') as urllist, open('output.jsonl','w') as outfile:
        for url in urllist:
            driver.get(url)
            time.sleep(2)
            total += 1

            try:
                data = e.extract(driver.page_source)

                if data:
                    
                    if not data["image"] and not data["image_alternative"] and not data["image_alternative_two"]:
                        print("No images..")

                    data["url"] = url

                    json.dump(data, outfile)

                    outfile.write("\n")

                    count += 1
            except Exception as e:
                with open('error_log.txt', 'a') as f:
                    f.write(f"An error occurred at url {url}: {str(e)}\n")
                    f.write(traceback.format_exc())
                    f.write("\n")
                print(f"An error occurred at url {url}: {str(e)}")
        
        current_time = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")

        with open(f'scrape_log_{current_time}.txt', 'w') as f:
            f.write(f"Scraped {count} / {total} URLs and skipped {skipped}")



def convert_from_jsonl_to_csv(json_file):
    # Open your jsonl file and read lines into a list
    with open(json_file, 'r') as json_file:
        data = [json.loads(line) for line in json_file]

        # Get the keys for csv header
        headers = data[0].keys()

    processed_data = []
        #data = json.loads(json_file)

    for line in data:

        # Handle prices
        if not line.get("price"):

            # Skip product entirely if no price and alternative price
            if not line.get("price_alternative"):
                continue

            # Pass alternative_price as price
            line["price"] = line["price_alternative"]

        # Remove alternative price    
        if "price_alternative" in line:
            del line["price_alternative"]


        # Handle images
        if not line.get("image"):
            if not line.get("image_alternative"):
                continue

            line["image"] = line["image_alternative"]

        if "image_alternative" in line:
            del line["image_alternative"]
        
        if "image_alternative_two" in line:
            del line["image_alternative_two"]


        # Handle author
        if not line.get("author"):
            if line.get("author_alternative"):
                line["author"] = line["author_alternative"]
                
        if "author_alternative" in line:
            del line["author_alternative"]

        processed_data.append(line)


    # Write to a csv file
    with open('output.csv', 'w', newline='', encoding='utf-8') as csv_file:
        writer = csv.DictWriter(csv_file, fieldnames=headers)
        writer.writeheader()
        writer.writerows(processed_data)


# TODO Make a log of urls parsed, in case of interruption. Continue where left off.
if __name__ == "__main__":

    arg_list =sys.argv

    if len(arg_list) == 1:
        print(
"""
You need to pass at least one argument: 
-u : to get all urls from given category
-s : to scrape all product data from list of urls
-c : to convert json to csv
""")


    if "-u" in arg_list:
        url = "https://www.amazon.com/s?i=stripbooks&bbn=283155&rh=n%3A283155%2Cp_n_condition-type%3A1294423011&s=featured-rank&dc&ds=v1%3AIEShJtG0YHyUGBqOMyF16IHOtTdIsXtErDXZXA%2F0QNA&qid=1689598053&ref=sr_ex_n_1"
        pages = input("How many pages?")
        get_urls_from_category(url, int(pages))

    
    if "-s" in arg_list:
        scrape_urls()
    

    if "-c" in arg_list:
        convert_from_jsonl_to_csv("output.jsonl")



    
