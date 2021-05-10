from typing_extensions import final
from selenium import webdriver
import time
import pandas as pd



class homeDepotScraper:

## General methods
    def __init__(self):
        self.driver = driver = webdriver.Firefox(executable_path = r"C:\Users\grzeg\OneDrive\Pulpit\Point72\geckodriver.exe")
        ## Maximizing window
        self.driver.maximize_window()

    def get_homepage(self):
         ## Going to homedepot home page
        self.driver.get("https://www.homedepot.com/")
        time.sleep(2)

    def select_store(self, postal_code):
        ## Function used to select the store based on the postal code - When full name is used for searching, nothing is found. 

        ## Selecting your shop
        shop_selector = self.driver.find_element_by_xpath("//div[@class='MyStore__store']")
        shop_selector.click()

        time.sleep(0.5)
        ## It provides us with pop-up window on which we need to click Find Other Stores
        find_other_stores = self.driver.find_element_by_xpath("//div[@id='myStoreDropdown']//a[./span[contains(text(), 'Find Other Stores')]]")
        find_other_stores.click()

        time.sleep(0.5)
        ## Now we need to input our desired store's location
        store_input_field = self.driver.find_element_by_xpath("//input[@id='myStore-formInput']")

        ## Postal-code is used for search - the direct name throws an nothing found error
        store_input_field.send_keys(postal_code)

        store_search_button = self.driver.find_element_by_xpath("//button[@id='myStore-formButton']")
        store_search_button.click()

        time.sleep(0.5)
        ## Now we just need to select our store (a few will be listed, however the one best matching with our postal code will be listed as first)
        select_store_button = self.driver.find_element_by_xpath("""//button[@class='localization__select-this-store bttn-outline bttn-outline--dark']""")

        select_store_button.click()

        ## We should wait a while before proceding to further actions
        time.sleep(2)
        ## After that the store is selected and we can proceed with scraping data for a specific product-manufacturer

    def get_subdepartment_data(self, subdepartment_name):
        ## This code is responsible for taking us to the page related to the specific subdepartment (dishwashers, refrigerators, mattresses)

        ## Finding All Departments on navigation bar and clicking it
        departments_list = self.driver.find_element_by_xpath("//a[@data-id='departmentsFlyout']")
        departments_list.click()

        ## We need to wait for a page to fully load - We will be sure about that when the page's title is available. 
        # wait = WebDriverWait(self.driver, timeout = 3)
        # department_page = wait.until(EC.presence_of_element_located((By.XPATH, "//h1[@class='page-header]")))
        time.sleep(3)

        ## After that we get a page with all the departments and subdepartments available. From here we can choose between our needs 
        ## (Dishwashers, Refrigeators, Mattresses in this case). 
        subdepartment_name = "'{}'".format(subdepartment_name)
        print(subdepartment_name)
        subdep = self.driver.find_element_by_xpath("//a[text() = {}]".format(subdepartment_name))
        subdep.click()

## Dishwasher methods
    def get_dishwasher_links(self):
        ## This code is responsible for getting producer-specific links for dishwashers, which will be later passed for scraping. 

        # We want to browse through all dishwashers (later filtering by brands). We need to choose Shop All Dishwashers option first
        # There are 2 elements with this property on the page but it doesn't matter which we click on.
        all_dishwashers = self.driver.find_element_by_xpath("//a[contains(text(), 'Shop All Dishwashers')]")
        all_dishwashers.click()

        time.sleep(2)

        ## Now the key-part is filtering. Filters for different properties are captured inside divs with class='dimension'. 
        ## Locating all dimensions - which stand for filtering boxes 
        dimensions = self.driver.find_elements_by_xpath("//div[@class='dimension']")

        ## For each dimension (filtering box) we can find its name and save it to dictionary
        dimensions_dict = {}
        for dimension in dimensions:
            dimension_name = dimension.find_element_by_xpath('.//h2').text
            dimensions_dict[dimension_name] = dimension

        ## From the dictionary created in a previous step we can now choose which filtering box we want to use - Brand in our case
        ## Structure of each dimension is following
        ## -- <div class='grid'>
        ## ---- <div class='grid'>
        ## ---- <div class='grid'>
        ## Inside each div there is one main <div class='grid'> 
        ## inside of which there are 2 <div class='grid'>, the first contains the name of the filter (e.g.Brand), 
        ## the second is used for filtering. The second is the one we need
        brand = dimensions_dict['Brand'].find_element_by_xpath(".//div[@class='grid']//div[@class='grid'][2]")

        ## Now we have our brand filtering box located, but tp select desired brands we need to unhide all our options with + See All button
        brand_see_all = brand.find_element_by_xpath(".//a[@class='dimension__see-all']")
        brand_see_all.click()

        ## Brands' data is available inside <div class='dimension__item col__12-12'>
        brands = brand.find_elements_by_xpath(".//div[@class='dimension__item col__12-12']")

        ## For each brand div, brand name and a link to brand-specific products can be retrieved

        ## Again we can create a dictionary with brand name and checkbox webelement to easily navigate through them in future 
        brands_dictionary = {}

        for brand in brands:
            ## Getting checkbox location
            link = brand.find_element_by_xpath(".//a[@class='refinement__link']").get_attribute('href')
            brand_name = brand.find_element_by_xpath(".//h3").text
            
                
            brands_dictionary[brand_name] = link

        return brands_dictionary

    def extract_metadata_dishwashers(self, shop_ref, selected_brand, product_info):
        ## Each page with dishwashers data, consists of standarized blocks which contain the same set of information for different dishwashers
        ## This function is used to retrieve necessary information for each dishwasher

        ## Getting rating, this is quite tricky, as rating is shown in page as stars (0-min;5max). 
        ## However, there is style:width property for that star representation, out of which we can scrape the actual %rating
        rating = product_info.find_element_by_xpath(".//span[@class='stars']").get_attribute('style')
        rating = rating.replace("width:", "")
        rating = rating.replace("%", "").replace(";", "")
        rating = float(rating)
        
        number_of_rates = product_info.find_element_by_xpath(".//span[@class='product-pod__ratings-count']").text
        number_of_rates = number_of_rates.replace(")", "").replace("(", "")
        number_of_rates = int(number_of_rates)
        
        model = product_info.find_element_by_xpath(".//div[@class='product-pod__model']").text
        
        ## The price is also not available in a straightforward way, so it must be obtained in steps
        price_elements = [price.text for price in product_info.find_elements_by_xpath(".//div[@class='price-format__main-price']//span")]
        # sometimes there is no price, so further formatting actions cannot be completed
        if len(price_elements) == 0:
            price = None
        else:
            price_elements.remove("$")
            ## Now we can join the rest into a final number and have it as float
            price = float(".".join(price_elements))
        
        
        
        ## In the end we can access additional information provided
        additional_infos = product_info.find_elements_by_xpath(".//div[@class='kpf__specblock kpf__specblock--simple kpf__specblock--one-column col__12-12 col__12-12--xs']")
        
        ## Attribute names and their values are separated by \n, so we split on this
        additional_infos = [info.text.split("\n")[1] for info in additional_infos]
        tub_material, sound_rating, height, size, control_location = additional_infos
        
    
        return (shop_ref, selected_brand, rating, number_of_rates, model, price, tub_material, sound_rating, height, size, control_location)

    def scrape_dishwasher_data(self, link, shop_ref, selected_brand):
        
        ## First we load a page with dishwashers from a specific manufacturer
        self.driver.get(link)
        time.sleep(1)

        ## Creating empty list which will be used for saving final results
        dishwasher_data = []
        ## Next we need to create a logic for pagination, if there is such
        paginations = self.driver.find_elements_by_xpath("//li[@class='hd-pagination__item']")

        if len(paginations) == 0:
            ## Now we can retrieve info for all the products available at the page
            products_info = self.driver.find_elements_by_xpath("//div[@class='desktop product-pod']")
            for product_info in products_info: 
                results = self.extract_metadata_dishwashers(shop_ref, selected_brand, product_info)
                print(results, "\n")
                dishwasher_data.append(results)
        
        else: 
            ## In case there are other pages, we can get their urls
            pages = [page.find_element_by_xpath("./a").get_attribute('href') for page in paginations]

            for page in pages: 
                self.driver.get(page)
                time.sleep(1)
                products_info = self.driver.find_elements_by_xpath("//div[@class='desktop product-pod']")

                for product_info in products_info: 
                    results = self.extract_metadata_dishwashers(shop_ref, selected_brand, product_info)
                    print(results, "\n")
                    dishwasher_data.append(results)
        
        return dishwasher_data

## Refrigerator methods
    def get_refrigerator_links(self):
        ## Structure of refrigerator page is slightly different then this for dishwashers. The links for producer-specific pages must be then obtained in a different manner
        brands = self.driver.find_elements_by_xpath("//p[contains(text(), 'Top Refrigerator Brands')]//following-sibling::ul//li//a")
        brands_dictionary = {brand.get_attribute('text'): brand.get_attribute('href') for brand in brands}
        return brands_dictionary

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
            dishwasher_data = scraper.scrape_dishwasher_data(link, shop_details, selected_brand)
            final_results.append(dishwasher_data)

    final_results = [x for y in final_results for x in y]
    
    df = pd.DataFrame(final_results, columns=['Shop', 'Producer', 'Rating(%)', 'Number of votes', 'Model', 'Price', 'Tub Material', 
    'Sound Rating', 'Height', 'Size', 'Control Location'])

    print(df)
        

## User inputs for dishwashers
selected_stores = {

    "Manhattan 59th Street #6177": "NY 10022", 
    "Lemmon Ave #0589": "TX 75209"

}

## There are 3 different LG brands, although LG STUDIO and LG SIGNATURE seems to be some legacy ones. 
selected_brands_dishwasher = ["Samsung", "LG Electronics", "LG STUDIO", "LG SIGNATURE"]


# dishwasher_scraper(selected_stores, selected_brands_dishwasher)

########## Refrigeator scraper

selected_brands_refrigerator = ['Whirpool', 'GE Appliances']

def refrigerator_scraper(selected_stores, selected_brands_refrigerator):
    
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
        scraper.get_subdepartment_data('Refrigerators')

        ## Getting links with dishwashers produced by specific manufacturers
        brands_dictionary = scraper.get_refrigerator_links()

        print(brands_dictionary)


refrigerator_scraper(selected_stores, selected_brands_refrigerator)