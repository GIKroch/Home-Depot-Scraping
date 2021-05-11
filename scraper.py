from os import link
from typing_extensions import final
from selenium import webdriver
import time
import pandas as pd
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC



class homeDepotScraper:

## General methods
    def __init__(self):
        self.driver = webdriver.Firefox(executable_path = r"C:\Users\grzeg\OneDrive\Pulpit\Point72\geckodriver.exe")
        ## Maximizing window
        self.driver.maximize_window()

    def get_homepage(self):
         ## Going to homedepot home page
        self.driver.get("https://www.homedepot.com/")

    def select_store(self, postal_code):
        ## Function used to select the store based on the postal code - When full name is used for searching, nothing is found. 

        ## Selecting your shop
        shop_selector = WebDriverWait(self.driver, timeout = 60).until(
            EC.element_to_be_clickable((By.XPATH,"//div[@class='MyStore__store']"))
        )
        shop_selector.click()

        ## It provides us with pop-up window on which we need to click Find Other Stores
        find_other_stores = WebDriverWait(self.driver, timeout = 60).until(
            EC.element_to_be_clickable((By.XPATH,"//div[@id='myStoreDropdown']//a[./span[contains(text(), 'Find Other Stores')]]"))
        )
        find_other_stores.click()

        
        ## Now we need to input our desired store's location
        store_input_field = WebDriverWait(self.driver, timeout = 60).until(
            EC.presence_of_element_located((By.XPATH, "//input[@id='myStore-formInput']"))
        )
        ## Postal-code is used for search - the direct name throws an nothing found error
        store_input_field.send_keys(postal_code)

        store_search_button = self.driver.find_element_by_xpath("//button[@id='myStore-formButton']")
        store_search_button.click()

        ## Now we just need to select our store (a few will be listed, however the one best matching with our postal code will be listed as first)
        select_store_button = WebDriverWait(self.driver, timeout = 60).until(
            EC.presence_of_element_located((By.XPATH, "//button[@class='localization__select-this-store bttn-outline bttn-outline--dark']"))
        )

        select_store_button.click()
        ## After that the store is selected and we can proceed with scraping data for a specific product-manufacturer

    def get_subdepartment_data(self, subdepartment_name):
        print(subdepartment_name)
        ## This code is responsible for taking us to the page related to the specific subdepartment (dishwashers, refrigerators, mattresses)

        ## Finding All Departments on navigation bar and clicking it
        departments_list = WebDriverWait(self.driver, timeout = 60).until(
            EC.presence_of_element_located((By.XPATH, "//a[@data-id='departmentsFlyout']"))
        )
        departments_list.click()

        
        ## After that we get a page with all the departments and subdepartments available. From here we can choose between our needs 
        ## (Dishwashers, Refrigeators, Mattresses in this case). 
        subdepartment_name = "'{}'".format(subdepartment_name)
        subdep = WebDriverWait(self.driver, timeout = 60).until(
            EC.presence_of_element_located((By.XPATH, "//a[text() = {}]".format(subdepartment_name)))
        )
        subdep.click()


## Getting brand links methods - get_brand_links applies to Dishwashers and Refrigerators, get_brand_links_mattresses applies to mattresses - due to a slightly different page structure
    def get_brand_links(self, keyword):
        ## After getting a page for a specific product (refrigerator, dishwasher), we will now get links for producer specific pages for the products 
        ## The key-word used for this task differs between the products, so it is passed as a function's argument
        ## For refrigerators it's Top Refrigerator Brands, for dishwashers it's just Brand
        keyword = f"'{keyword}'"
        
        brands =  WebDriverWait(self.driver, timeout = 60).until(
            EC.presence_of_element_located((By.XPATH, f"//p[contains(text(), {keyword} )]//following-sibling::ul//li//a"))
        )
        brands = self.driver.find_elements_by_xpath(f"//p[contains(text(), {keyword} )]//following-sibling::ul//li//a")

        ## Sometimes the producer name is returned along with a trademark sign ®, for simplification we will remove it
        self.brands_dictionary = {brand.get_attribute('text').replace("®",""): brand.get_attribute('href') for brand in brands}

        return self.brands_dictionary

    def get_brand_links_mattresses(self):
        
        # time.sleep(2)
        # self.driver.execute_script("window.scrollBy(0,4000)", "")
        # time.sleep(1)

        ## First we need to find brand selection box and click See All
        self.driver.execute_script("window.scrollBy(0,4000)", "")
        time.sleep(1)

        see_all_button = WebDriverWait(self.driver, timeout = 60).until(
            EC.element_to_be_clickable((By.XPATH, "//div[@class='dimension' and .//h2[text()='Brand']]//a[@class='dimension__see-all']"))
        )
        see_all_button.click()
        
        brand_dimension = WebDriverWait(self.driver, timeout = 60).until(
            EC.presence_of_element_located((By.XPATH, "//div[@class='dimension' and .//h2[text()='Brand']]//div[@class='dimension__item col__12-12']"))
        )
        brand_dimension = self.driver.find_elements_by_xpath("//div[@class='dimension' and .//h2[text()='Brand']]//div[@class='dimension__item col__12-12']")
        brands_dictionary = {}

        for brand_row in brand_dimension:
            brand = brand_row.find_element_by_xpath(".//h3[@class='refinement__link']").text
            brand_link = brand_row.find_element_by_xpath(".//a[@class='refinement__link']").get_attribute('href')
            brands_dictionary[brand] = brand_link
        self.brands_dictionary = brands_dictionary

        return self.brands_dictionary

    def get_product_links(self, selected_brands):
        
        ## This method is used to obtain all the links for a specific product for a particular producent. 
        ## If we are working with Dishwashers, and brand are LG and Samsung, in this function the links to all LG and Samsung dishwashers will be gathered

        product_links = {}
        ## Getting product links for a specific brand
        for selected_brand in selected_brands:
            brand_page = self.brands_dictionary[selected_brand]
            self.driver.get(brand_page)
            time.sleep(1)

            # First we need to create a logic for pagination, if there is such
            paginations = self.driver.find_elements_by_xpath("//li[@class='hd-pagination__item']")

            # Defining links_per_brand list
            
            

            if len(paginations) == 0:
                # scroll_control variable is introduced as the page must be scrolled once to obtain all links available
                scroll_control = 0
                links_per_brand = []
                
                while scroll_control < 4:
                ## We get all the links of a specific product for a particular producer
                    links = WebDriverWait(self.driver, timeout = 60).until(
                        EC.presence_of_element_located((By.XPATH, "//a[@class='header product-pod--ie-fix']"))
                    )
                    links = [link.get_attribute('href') for link in self.driver.find_elements_by_xpath("//a[@class='header product-pod--ie-fix']")]
                    # links = self.driver.find_elements_by_xpath("//a[@class='header product-pod--ie-fix']")
                    # links = [link.get_attribute('href') for link in links]
                    links_per_brand.append(links)
                    time.sleep(0.1)
                    self.driver.execute_script("window.scrollBy(0,3000)", "")
                    scroll_control += 1

                links_per_brand = [x for y in links_per_brand for x in y]
                links_per_brand = list(set(links_per_brand))
                product_links[selected_brand] = links_per_brand
            
            else:
                pages = [page.find_element_by_xpath("./a").get_attribute('href') for page in paginations]
                links_per_brand = []

                for page in pages: 
                    self.driver.get(page)
                     # scroll_control variable is introduced as the page must be scrolled once to obtain all links available
                    scroll_control = 0  
                
                    while scroll_control < 4:
                    ## We get all the links of a specific product for a particular producer
                        links = WebDriverWait(self.driver, timeout = 60).until(
                            EC.presence_of_element_located((By.XPATH, "//a[@class='header product-pod--ie-fix']"))
                        )
                        links = [link.get_attribute('href') for link in self.driver.find_elements_by_xpath("//a[@class='header product-pod--ie-fix']")]
                        # links = [link.get_attribute('href') for link in links]
                        links_per_brand.append(links)
                        time.sleep(0.1)
                        self.driver.execute_script("window.scrollBy(0,3000)", "")
                        scroll_control += 1
                
                links_per_brand = [x for y in links_per_brand for x in y]
                links_per_brand = list(set(links_per_brand))
                product_links[selected_brand] = links_per_brand

        self.product_links = product_links

        return product_links

    def get_other_details(self, detail_name):
        ## A lot of product-related information is provided in the tabular form. With this function, user can retrieve any existing information.
        detail_name_formatted = f"'{detail_name}'"

        ## This error handling is introduced in case some information is not available
        try:
            # element = self.driver.find_element_by_xpath(f"//div[text()={detail_name_formatted}]//parent::div")
            element = self.driver.find_element_by_xpath(f"//div[@class='specifications__wrapper']//div[text()={detail_name_formatted}]//following-sibling::div")
            detail = element.text
        except:
            detail = None

        return detail

    def get_metadata(self):
        ## Method to get all desired product information
        ## getting metadata
        ## User specifies other detiles as a list of details. 

        ## For each find_element we use, try/except, just in case some element is not found, to prevent the whole scraping from braking

        try:
            model = self.driver.find_element_by_xpath("//h2[contains(text(),'Model')]").text
        except:
            model = None

        try:
            rating = self.driver.find_element_by_xpath("//span[@class='stars']").get_attribute('style')
            rating = rating.replace("width: ", "").replace("%", "").replace(";","")
            rating = float(rating)
        except:
            rating = None

        try:
            number_of_rates = self.driver.find_element_by_xpath("//span[@class='product-details__review-count']").text
            number_of_rates = int(number_of_rates.replace("(","").replace(")",""))
        except:
            number_of_rates = None

        try:
            is_on_display = self.driver.find_elements_by_xpath("//span[text()='On Display']")
            ## If it's not on display, an element won't be found, so in such a case we set it to No. Otherwise, it's Yes (On Display)
            if len(is_on_display) == 0:
                is_on_display = "No"
            else:
                is_on_display = "Yes"
        except:
            is_on_display = None

        # ## The price is also not available in a straightforward way, so it must be obtained in steps
        try:
            price_elements = self.driver.find_elements_by_xpath(".//div[@class='price-format__large price-format__main-price']")[0]
            price_elements = [element.text for element in price_elements.find_elements_by_xpath(".//span")]

            ## We need to remove dollar sign and some empty string which are found in the same block as the price
            price_elements.remove("$")
            price_elements = [x for x in price_elements if x!= '']

            ## Now we can join the rest into a final number and have it as float
            price = float(".".join(price_elements))
        except:
            price = None

        
        ## Creating the list with the results for a specific product
        results = [model, rating, number_of_rates, price, is_on_display]

        ## We need to scroll-down to get other details
        if self.product_type == 'Mattresses':
            self.driver.execute_script("window.scrollBy(0,2000)", "")
        else:
            self.driver.execute_script("window.scrollBy(0,4750)", "")
        time.sleep(1)

        ## Now we are appending other details to results
        for detail_name in self.other_details: 
            detail = self.get_other_details(detail_name)
            results.append(detail)
        
        return results

    def get_metadata_all(self, other_details, product_type):
        
        self.product_type = product_type
        final_results = []
        ## Now we are running get_metadata for all the links obtained in get_product_links
        self.other_details = other_details

        for producer, product_links in self.product_links.items():

            for product_link in product_links:
                
                self.driver.get(product_link)
                time.sleep(2)
                results = self.get_metadata()
                results = [producer, product_link] + results
                # print(results)
                final_results.append(results)
                
                
            
        
        return final_results

   

######### Dishwasher Scraper
def dishwasher_scraper(selected_stores, selected_brands):
    
    ## Initiating scraping class
    scraper = homeDepotScraper()

    final_results = []
    ## At the beginning we are selecting the store we want to focus our scraping on. 
    ## Code, which specifies the store uses postal codes to find correct ones. 
    ## Therefore selected_stores dictionary (user-defined) is used for this task. 

    ## The scraping will be done in a loop for each store selected
    for shop_ref, postal_code in selected_stores.items():
        
        shop_details = shop_ref + " " + postal_code

        ## We start from getting the homepage
        scraper.get_homepage()

        print(shop_ref)
        ## Selecting a store
        scraper.select_store(postal_code)

        ## Going to dishwashers section
        scraper.get_subdepartment_data("Dishwashers")

        ## Getting links with dishwashers produced by specific manufacturers
        brands_dictionary = scraper.get_dishwasher_links()

        for selected_brand in selected_brands:
            link = brands_dictionary[selected_brand]
            data = scraper.scrape_data(link, shop_details, selected_brand)
            final_results.append(data)

    final_results = [x for y in final_results for x in y]
    
    df = pd.DataFrame(final_results, columns=['Shop', 'Producer', 'Rating(%)', 'Number of votes', 'Model', 'Price', 'Tub Material', 
    'Sound Rating', 'Height', 'Size', 'Control Location'])

    print(df)
        

def scraper(selected_stores, selected_brands, product_type, other_details):
    
    ## Initiating scraping class
    scraper = homeDepotScraper()

    final_results = []
    ## At the beginning we are selecting the store we want to focus our scraping on. 
    ## Code, which specifies the store uses postal codes to find correct ones. 
    ## Therefore selected_stores dictionary (user-defined) is used for this task. 

    ## The scraping will be done in a loop for each store selected
    for shop_ref, postal_code in selected_stores.items():
        
        shop_details = shop_ref + " " + postal_code

        ## We start from getting the homepage
        scraper.get_homepage()

        print(shop_ref)
        ## Selecting a store
        scraper.select_store(postal_code)

        if product_type == 'Dishwashers':
            ## Going to refrigerators section
            scraper.get_subdepartment_data('Dishwashers')
            ## Getting links with refrigerators produced by specific manufacturers
            scraper.get_brand_links('Brands')

        elif product_type == 'Refrigerators':
            scraper.get_subdepartment_data('Refrigerators')
            scraper.get_brand_links("Top Refrigerator Brands")

        elif product_type == 'Mattresses':
            scraper.get_subdepartment_data('Mattresses')
            scraper.get_brand_links_mattresses()
        else:
            pass

        ## Now we are getting direct links to products 
        product_links = scraper.get_product_links(selected_brands)
        
        ## Now we are running a method which extracts all relevant information for obtained links. 
        ## For the function to run properly, we need to specify the list other_details
        ## Inside which user can specify the name of the attributes, one wants to retrieve from a specific product page.
        ## Some of the attributes are returned on default:  model, rating, number_of_rates, price, is_on_display
        ## The rest must be specified by the user - For the names of the attributes scroll down to where the tables with information are (mid-page)

        ## For simplification we retrieve 5 additional attributes, can be many more
        results = scraper.get_metadata_all(other_details, product_type)
        
        ## Adding shop name to final results
        results = [[shop_details] + x for x in results]
        final_results.append(results)
    
    final_results = [x for y in final_results for x in y]

    column_names = ['Shop', 'Producer', 'Link', 'Model', 'Rating (%)', 'Number of Rates', 'Price', 'On Display'] + other_details

    df = pd.DataFrame(final_results, columns = column_names)

    df.to_excel(f'{product_type}.xlsx', index = False)

def scraper_mattresses(selected_stores, selected_brands, product_type, other_details):
    
    ## Initiating scraping class
    scraper = homeDepotScraper()

    final_results = []
    ## At the beginning we are selecting the store we want to focus our scraping on. 
    ## Code, which specifies the store uses postal codes to find correct ones. 
    ## Therefore selected_stores dictionary (user-defined) is used for this task. 

    ## The scraping will be done in a loop for each store selected
    for shop_ref, postal_code in selected_stores.items():
        
        shop_details = shop_ref + " " + postal_code

        ## We start from getting the homepage
        scraper.get_homepage()

        print(shop_ref)
        ## Selecting a store
        scraper.select_store(postal_code)

        scraper.get_subdepartment_data('Mattresses')
        scraper.get_brand_links_mattresses()



        ## Now we are getting direct links to products 
        product_links = scraper.get_product_links(selected_brands)
        print(product_links)

        ## Now we are running a method which extracts all relevant information for obtained links. 
        ## For the function to run properly, we need to specify the list other_details
        ## Inside which user can specify the name of the attributes, one wants to retrieve from a specific product page.
        ## Some of the attributes are returned on default:  model, rating, number_of_rates, price, is_on_display
        ## The rest must be specified by the user - For the names of the attributes scroll down to where the tables with information are (mid-page)

    #     ## For simplification we retrieve 5 additional attributes, can be many more
    #     results = scraper.get_metadata_all(other_details)
        
    #     ## Adding shop name to final results
    #     results = [[shop_details] + x for x in results]
    #     final_results.append(results)
    
    # final_results = [x for y in final_results for x in y]

    # column_names = ['Shop', 'Producer', 'Link', 'Model', 'Rating (%)', 'Number of Rates', 'Price', 'On Display'] + other_details

    # df = pd.DataFrame(final_results, columns = column_names)

    # df.to_excel(f'{product_type}.xlsx', index = False)



## User inputs for dishwashers
selected_stores = {

    "Manhattan 59th Street #6177": "NY 10022", 
    "Lemmon Ave #0589": "TX 75209"

}

## Scraping dishwashers
selected_brands_dishwashers = ["Samsung", "LG"]
other_details_dishwasher = ['Color/Finish', 'Energy Consumption (kWh/year)','Decibel (Sound) Rating', 'Product Height (in.)', 'Dishwasher Size']
scraper(selected_stores, selected_brands_dishwashers, "Dishwashers",other_details_dishwasher)

## Scraping refrigerators
selected_brands_refrigerators = ['Whirlpool', 'GE Appliances']
other_details_refrigerators = ['Appliance Type', 'Color/Finish', 'Energy Consumption (kWh/year)', 'Refrigerator Capacity (cu. ft.)', 'Product Height (in.)']
scraper(selected_stores, selected_brands_refrigerators, "Refrigerators",other_details_refrigerators)

## Scraping mattresses
selected_brands_mattresses = ['Sealy']
other_details_mattresses = ['Size', 'Mattress Fill Type', 'Box Spring Required', 'Mattress Thickness (in.)', 'Mattress Top', 'Features', 'Product Weight (lb.)']
scraper(selected_stores, selected_brands_mattresses, "Mattresses",other_details_mattresses)