import requests
from bs4 import BeautifulSoup
import json
from itertools import combinations_with_replacement

def card_soup(soup : BeautifulSoup) :
    card_info = soup.find(id="tabContent-info")
    card_table = card_info.find_all_next("div", {"class": "info-list-container"})[0]
    ct_right = card_table.find_all_next("dd", {"class": "col-6 col-xl-7"}) # len 9
    ct_left = card_table.find_all_next("dt", {"class": "col-6 col-xl-5"}) # len 9

    card_values = dict()
    for i in range(4, 9) :
        if i >= len(ct_left) or i >= len(ct_right) :
            prop, value = "BAD_%d" % (i-3), 0.0

        else :
            prop = ct_left[i].string
            try :
                value = float(ct_right[i].string.split(" ")[0].replace(",", ".")) # validate, contains sapce and float parse
            except ValueError :
                print("\t-> %s cloudn't be converted to number." % (ct_right[i].string))
                prop, value = "BAD_%d" % (i-3), 0.0
       
        card_values[prop] = value

    # print(card_values, sep = "\n")
    rarity = ct_right[0].find_next("span", {"class": "icon"})['title']
    # print(rarity)

    return {rarity: card_values}


def download_card_info(tcg_name: str, set_name: str, card_name: str) :
    url = "https://www.cardmarket.com/en/%s/Products/Singles/%s/%s" % (tcg_name, set_name, card_name)
    try :
        page = requests.get(url)
        # validate status code
        print("%4s %s" % (page.status_code, url))

    except Exception as e: 
        print(e)
        return {}

    # print(page.content)
    soup = BeautifulSoup(page.content, "html.parser")
    return card_soup(soup)


def get_card_info(cards_json: dict, tcg_name: str, set_name: str, card_name: str) :
    if (cards_json[tcg_name][set_name][card] == {}) :
        return download_card_info(tcg_name, set_name, card_name)

    return cards_json[tcg_name][set_name][card]


def card_list_soup(soup: BeautifulSoup, tcg_name: str, set_name: str) :
    all_cards = []
    all_products = soup.findAll('a', 
        href=lambda x: x and x.startswith("/en/%s/Products/Singles/%s/" % (tcg_name, set_name)))

    for product in all_products :
        all_cards.append(product['href'].split("/")[6])
        # print(product['href'].split("/")[6])

    return all_cards


def get_card_names_by_set(tcg_name: str, set_name: str) :
    cards_filename="./card_names.json"

    with open(cards_filename, "r") as all_cards_f :
        cards_json = json.load(all_cards_f)

    if not tcg_name in cards_json :
        cards_json[tcg_name] = {}

    if not set_name in cards_json[tcg_name] :
        cards_json[tcg_name][set_name] = {}

    elif (cards_json[tcg_name][set_name] != {}) :
        return cards_json[tcg_name][set_name]

    url = "https://www.cardmarket.com/en/%s/Products/Singles/%s" % (tcg_name, set_name)
    url_is_available = True
    i = 1
    page_cont = ""
    all_card_names = []

    while url_is_available :
        try :
            page = requests.get(url)
            # validate status code
            print("%4s %s" % (page.status_code, url))
            url_is_available = page.status_code != "404"

            page_cont = page.content

        except Exception as e: 
            print(e)
            url_is_available = False
            break

        soup = BeautifulSoup(page_cont, "html.parser")
        page_cards = card_list_soup(soup, tcg_name, set_name)

        for card in page_cards :
            cards_json[tcg_name][set_name][card] = download_card_info(
                tcg_name, set_name, card)

        all_card_names += page_cards

        i += 1
        url_is_available = page_cards != []
        url = "https://www.cardmarket.com/en/%s/Products/Singles/%s?site=%d" % (tcg_name, set_name, i)

    with open(cards_filename, "w") as all_cards_new :
        all_cards_new.write(json.dumps(cards_json,  indent = 4))

    return all_card_names


def main() :
    price_dict = dict()

    all_names = get_card_names_by_set("YuGiOh", "Photon-Hypernova")
    for card in all_names :
        rar = list(all_names[card].keys())[0]
        val = list(list(all_names[card].values())[0].values())[0]

        if rar in price_dict :
            l = price_dict[rar].copy()
            l.append(val)
            price_dict[rar] = l
        else :
            price_dict[rar] = []


    perm1 = combinations_with_replacement(price_dict["Ultra Rare"], 4)
    perm2 = combinations_with_replacement(price_dict["Secret Rare"], 2)
    all_sells = []
    for i, j in zip(perm1, perm2) :
        all_sells.append(round(sum(i)+sum(j),2))

    all_sells.sort()
    print(all_sells)
    """
    avg_secret = sum(price_dict["Secret Rare"]) / len(price_dict["Secret Rare"])
    avg_ultra  = sum(price_dict["Ultra Rare"])  / len(price_dict["Ultra Rare"])

    avg_booster = 4 * avg_ultra + 2 * avg_secret

    print("Secret: " + str(avg_secret))
    print("Ultra: " + str(avg_ultra))
    print()
    print("Booster: " + str(avg_booster))
    """

if __name__ == "__main__" :
    main()
