#!/usr/bin/python
# coding=utf-8
# encoding=utf8
import datetime
import json
import os
import time
import urllib.parse
from difflib import SequenceMatcher

from osint_sources.recognition import *
from parsel import Selector
from selenium import webdriver
from selenium.webdriver.chrome.options import Options


def twitter(name_to_search, page_number, knownimage, verbose):
    placeToSearch = 'twitter.com'
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")

    chrome_path = './chromedriver'
    driver = webdriver.Chrome(chrome_path, chrome_options=chrome_options)

    people_list = []
    for i in range(int(page_number)):
        driver.get("https://www.google.com/search?q=site:" + placeToSearch + "+AND+" + name_to_search + "&start=" + str(
            10 * i))
        search = driver.find_elements_by_tag_name('a')
        time.sleep(10)

        for s in search:
            href = s.get_attribute('href')
            if href != None:
                if "https://twitter.com/" in href:
                    if "/status/" not in href and "/media" not in href and "/hashtag/" not in href and "webcache.googleusercontent.com" not in href and "google.com" not in href:
                        people_list.append(href)
                    elif "/hashtag/" not in href and "webcache.googleusercontent.com" not in href and "google.com" not in href:
                        if "/status/" in href:
                            people_list.append(href.split("/status/")[0])
                        elif "/media" not in s.text:
                            people_list.append(href.split("/media")[0])

    people_list = set(people_list)
    now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    if not os.path.isdir("data/twitter"):
        os.mkdir("data/twitter");

    path = os.path.join('data/twitter', str(now) + '_twitter_data.json')
    jsonData = []
    userLink = set()
    for p in people_list:
        if verbose:
            print(
                "*******************************************************************************************************")
            print(p)
        driver.get(p)
        driver.implicitly_wait(50)
        time.sleep(2)

        sel = Selector(text=driver.page_source)

        name = sel.xpath(
            '//*[@id="react-root"]/div/div/div[2]/main/div/div/div/div/div/div[2]/div/div/div[1]/div/div[2]/div/div/div[1]/div/span[1]/span/text()').extract_first()
        link = p
        description = sel.xpath(
            '//*[@id="react-root"]/div/div/div[2]/main/div/div/div/div/div/div[2]/div/div/div[1]/div/div[3]/div/div/span[1]/text()').extract_first()
        location = sel.xpath(
            '//*[@id="react-root"]/div/div/div[2]/main/div/div/div/div/div/div[2]/div/div/div[1]/div/div[4]/div/span[1]/span/span/text()').extract_first()
        member_since = sel.xpath(
            '//*[@id="react-root"]/div/div/div[2]/main/div/div/div/div/div/div[2]/div/div/div[1]/div/div[4]/div/span[2]/svg/text()').extract_first()
        born = sel.xpath(
            '//*[@id="react-root"]/div/div/div[2]/main/div/div/div/div/div/div[2]/div/div/div[1]/div/div[4]/div/span[2]/svg/text()').extract_first()
        webpage = sel.xpath(
            '//*[@id="react-root"]/div/div/div[2]/main/div/div/div/div/div/div[2]/div/div/div[1]/div/div[4]/div/a/text()').extract_first()
        image_url = sel.xpath(
            '//*[@id="react-root"]/div/div/div[2]/main/div/div/div/div/div/div[2]/div/div/div[1]/div/div[1]/a/div[1]/div[2]/div/img/@src').extract_first()
        if name == None:
            name = ""
        if str(link) not in userLink:
            userLink.add(link)
            nameParts = name_to_search.split(' ')
            isMatcher = False
            for n in nameParts:
                if SequenceMatcher(None, n, name).ratio() > 0.4 or SequenceMatcher(None, n,
                                                                                   str(link)).ratio() > 0.4 or n in str(
                    description).lower():
                    isMatcher = True

            if SequenceMatcher(None, name_to_search, name).ratio() > 0.4 or SequenceMatcher(None, name_to_search,
                                                                                            str(link)).ratio() > 0.4 or name_to_search in str(
                description).lower():
                isMatcher = True

            if isMatcher:
                userData = {}
                if verbose:
                    print("Name: " + str(name))
                    print("Link: " + str(link))
                    print("Description: " + str(description))
                    print("Location: " + str(location))
                    print("Member since: " + str(member_since))
                    print("Born: " + str(born))
                    print("Web: " + str(webpage))
                    print("Profile image url: " + str(image_url))
                    print('\n')
                    print('\n')

                if knownimage:
                    if not os.path.isdir("data/twitter/" + str(now) + "_images"):
                        os.mkdir("data/twitter/" + str(now) + "_images");
                    image = os.path.join("data/twitter/" + str(now) + "_images/" + str(link.split('.com/')[1]) + ".jpg")
                    try:
                        urllib.request.urlretrieve(image_url, image)
                        userData = {'storedImage': image, 'name': str(name), 'link': str(link),
                                    'description': str(description), 'location': str(location),
                                    'member_since': str(member_since), 'born': str(born), 'web': str(webpage),
                                    'image': str(image_url)}
                        jsonData.append(userData)
                    except:
                        pass
                else:
                    userData = {'name': str(name), 'link': str(link), 'description': str(description),
                                'location': str(location), 'member_since': str(member_since), 'born': str(born),
                                'web': str(webpage), 'image': str(image_url)}
                    jsonData.append(userData)

    with open(path, 'w+') as outfile:
        json.dump(jsonData, outfile)

    print("Results Twitter in: " + str(path))
    response = {'results': str(path)}

    if len(people_list) > 0:
        if knownimage:
            print("Compare similarity images.")
            face_identification(knownimage, './data/twitter/' + str(now) + '_images/')
            response['images'] = './data/twitter/' + str(now) + '_images/'
            response['recognized'] = './data/twitter/' + str(now) + '_images/recognized/'
    driver.quit()
    return response
