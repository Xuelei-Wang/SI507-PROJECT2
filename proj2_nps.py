#################################
##### Name: Shirley Wang
##### Uniqname: xuelw
#################################

from bs4 import BeautifulSoup
import requests
import json
import secrets # file that contains your API key


class NationalSite:
    '''a national site

    Instance Attributes
    -------------------
    category: string
        the category of a national site (e.g. 'National Park', '')
        some sites have blank category.
    
    name: string
        the name of a national site (e.g. 'Isle Royale')

    address: string
        the city and state of a national site (e.g. 'Houghton, MI')

    zipcode: string
        the zip-code of a national site (e.g. '49931', '82190-0168')

    phone: string
        the phone of a national site (e.g. '(616) 319-7906', '307-344-7381')
    '''
    def __init__(self, category, name, address, zipcode, phone):
        self.category = category
        self.name = name
        self.address = address
        self.zipcode = zipcode
        self.phone = phone

    def info(self):
        return f"{self.name} ({self.category}): {self.address} {self.zipcode}"


def build_state_url_dict():
    ''' Make a dictionary that maps state name to state page url from "https://www.nps.gov"

    Parameters
    ----------
    None

    Returns
    -------
    dict
        key is a state name and value is the url
        e.g. {'michigan':'https://www.nps.gov/state/mi/index.htm', ...}
    '''
    baseurl = "https://www.nps.gov"
    parturl = "https://www.nps.gov/index.htm"
    state_url_dict = {}
    text = make_request_with_cache(parturl)
    soup = BeautifulSoup(text, "html.parser")
    section = soup.find(class_="dropdown-menu SearchBar-keywordSearch")
    states = section.find_all("li")

    for state in states:
        content = state.find("a")
        name = content.text.lower().strip()
        url = baseurl + content["href"]
        state_url_dict[name] = url
    return state_url_dict
       

def get_site_instance(site_url):
    '''Make an instances from a national site URL.
    
    Parameters
    ----------
    site_url: string
        The URL for a national site page in nps.gov
    
    Returns
    -------
    instance
        a national site instance
    '''
    
    text = make_request_with_cache(site_url)
    soup = BeautifulSoup(text, "html.parser")
    header = soup.find(class_="Hero-titleContainer clearfix")
    name = header.find(class_="Hero-title").text.strip()
    category = header.find(class_="Hero-designation").text.strip()
    footer = soup.find(class_="ParkFooter-contact")
    city = footer.find(itemprop="addressLocality").text.strip()
    state = footer.find(itemprop="addressRegion").text.strip()
    zipcode = footer.find(itemprop="postalCode").text.strip()
    phone = footer.find(itemprop="telephone").text.strip()
    address = f"{city}, {state}"

    park_instance = NationalSite(name=name, category=category, address=address, zipcode=zipcode, phone=phone)

    return park_instance



def get_sites_for_state(state_url):
    '''Make a list of national site instances from a state URL.
    
    Parameters
    ----------
    state_url: string
        The URL for a state page in nps.gov
    
    Returns
    -------
    list
        a list of national site instances
    '''
    text = requests.get(state_url).text.strip()
    soup = BeautifulSoup(text, "html.parser")
    park_section = soup.find(id="list_parks")
    park_list = park_section.find_all(class_="col-md-9 col-sm-9 col-xs-12 table-cell list_left")
    park_instance = []
    for park in park_list:
        baseurl = "https://www.nps.gov"
        para = park.find("a")["href"]
        url = baseurl+para
        instance = get_site_instance(url)
        park_instance.append(instance)
    return park_instance


def get_nearby_places(site_object):
    '''Obtain API data from MapQuest API.
    
    Parameters
    ----------
    site_object: object
        an instance of a national site
    
    Returns
    -------
    dict
        a converted API return from MapQuest API
    '''

    baseurl = "http://www.mapquestapi.com/search/v2/radius"
    parameter = {"key":secrets.API_Key,
    "origin":site_object.zipcode,
    "radius":"10",
    "maxMatches":"10",
    "ambiguities":"ignore",
    "outFormat":"json"}
    resp = requests.get(baseurl,parameter)
    print("Fetching")
    results_object = resp.json()
    return results_object

CACHE_FILENAME = "new_cache.json"
CACHE_DICT = {}

def open_cache():
    try:
        cache_file = open(CACHE_FILENAME, 'r')
        cache_contents = cache_file.read()
        cache_dict = json.loads(cache_contents)
        cache_file.close()
    except:
        cache_dict = {}
    return cache_dict


def save_cache(cache_dict):
    dumped_json_cache = json.dumps(cache_dict)
    fw = open(CACHE_FILENAME,"w")
    fw.write(dumped_json_cache)
    fw.close()

def make_request_with_cache(url):
    CACHE_DICT = open_cache()
    if url in CACHE_DICT:
        print("Using cache")
        pass
    else:
        print("making new request")
        CACHE_DICT[url] = requests.get(url).text
        save_cache(CACHE_DICT)
    return CACHE_DICT[url]

def get_url_with_cache(states_dict, state):
    CACHE_DICT = open_cache()
    if state.capitalize() in CACHE_DICT:
        print("Using cache")
        pass
    else:
        print("making new request")
        state_url = states_dict[state]
        # sites_list = get_sites_for_state(state_url)
        CACHE_DICT[state.capitalize()] = state_url
        save_cache(CACHE_DICT)
    return CACHE_DICT[state.capitalize()]

def get_nearby_with_cache(instance):
    CACHE_DICT = open_cache()
    if instance.name in CACHE_DICT:
        print("Using cache")
        pass
    else:
        print("making new request")
        nearby = get_nearby_places(instance)
        CACHE_DICT[instance.name] = nearby
        save_cache(CACHE_DICT)
    return CACHE_DICT[instance.name]



if __name__ == "__main__":
    states_dict = build_state_url_dict()
    while 1>0:
        state = input(f"Enter a state name (e.g. Michigan, michigan) or 'exit':")
        sites_list = []
        if state == "exit":
            break
        else:
            if state.lower() in states_dict:
                state_url = get_url_with_cache(states_dict, state)
                # sites_list = get_sites_with_cache(states_dict, state)
                sites_list = get_sites_for_state(state_url)
                if sites_list != None:
                    print("------------------------------------")
                    print(f"List of national sites in {state.lower()}:")
                    print("------------------------------------")
                    for i in range(len(sites_list)):
                        print(f"[{i+1}] {sites_list[i].info()}")
            else:
                print("[Error]: Enter proper state name")
                continue
        second_input = ""
        while 1>0:
            number = input(f"Choose the number for detail search or 'exit' or 'back':")
            second_input = number
            if number == "exit":
                break
            elif number == "back":
                break
            elif number.isdigit() == True:
                if 0 < int(number) < (len(sites_list)+1):
                    instance = sites_list[int(number)-1]
                    nearby = get_nearby_with_cache(instance)
                    result = nearby["searchResults"]
                    if result != None:
                        print("---------------------------------")
                        print(f"Places near {instance.name}")
                        print("---------------------------------")
                    site_list = []
                    for i in range(len(result)):
                        name = result[i]["name"]
                        if "address" in result[i]["fields"]:
                            address = result[i]["fields"]["address"]
                            if address == "":
                                address = "no address"
                        else:
                            address = "no address"
                        if "city" in result[i]["fields"]:
                            city = result[i]["fields"]["city"]
                            if city == "":
                                city = "no city"
                        else:
                            city = "no city"
                        if "group_sic_code_name_ext" in result[i]["fields"]:
                            category = result[i]["fields"]["group_sic_code_name_ext"]
                            if category == "":
                                category = "no category"
                        else:
                            category = "no category"
                        print(f"- {name} ({category}): {address}, {city}")
                else:
                    print("[Error] Invalid input")
                    continue
            else:
                print("[Error] Invalid input")
                continue
        if second_input == "exit":
            break


    