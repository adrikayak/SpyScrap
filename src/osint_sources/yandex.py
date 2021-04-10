#!/usr/bin/python
# coding: utf-8
# encoding=utf8
import base64
import datetime
import json
import os
import random
import re
import sys
import time
import urllib.parse
import urllib.request
from urllib.request import Request, urlopen

import requests
from bs4 import BeautifulSoup
from fake_useragent import UserAgent
from osint_sources.recognition import *
from selenium import webdriver


def isCaptcha(driver):
    headers = driver.find_elements_by_tag_name('h1')
    for h in headers:
        if h.get_attribute('innerHTML') == "oops…":
            print('captcha detected')
            return (True)
    return (False)


def checkProxy(proxy):
    proxies = {
        "http": proxy,
        "https": proxy,
    }

    try:
        resp = requests.get("https://google.com", proxies=proxies, timeout=20)
        print("Google responses " + str(resp.status_code) + " in " + str(resp.elapsed.total_seconds()) + " seconds.")
        if ((resp.status_code != 200) or resp.elapsed.total_seconds() > 10):
            return 0
        else:
            return 1
    except:
        print("Error while checking the proxy: " + str(proxy))
        return 0


def crawlProxy():
    # Retrieve latest proxies
    ua = UserAgent()
    proxies = []
    proxies_req = Request('https://www.sslproxies.org/')
    proxies_req.add_header('User-Agent', ua.random)
    proxies_doc = urlopen(proxies_req).read().decode('utf8')

    soup = BeautifulSoup(proxies_doc, 'html.parser')
    proxies_table = soup.find(id='proxylisttable')

    # Save proxies in the array
    for row in proxies_table.tbody.find_all('tr'):
        proxies.append({'ip': row.find_all('td')[0].string, 'port': row.find_all('td')[1].string})

    invalidProxy = True
    proxy = None
    while invalidProxy:
        random_index = random.randint(0, len(proxies) - 1)
        random_proxy = proxies[random_index]
        proxy = str(random_proxy['ip']) + ":" + str(random_proxy['port'])
        chk = checkProxy(proxy)
        if chk:
            invalidProxy = False
    return proxy


def searchImages(driver, now, verbose):
    os.mkdir("data/yandex/" + str(now) + "_images")
    search = driver.find_elements_by_class_name('other-sites__item')
    j = 0
    print('Retrieving images')
    out = []
    for s in search:
        try:
            a = s.find_elements_by_tag_name('a')

            for i, al in enumerate(a):
                aclass = al.get_attribute('class')
                if aclass == 'other-sites__preview-link':
                    link = al.get_attribute('href')
                    if link != None and link != "":
                        name = os.path.join('data/yandex/' + str(now) + '_images', str(j) + "-yandex.jpg")
                        j = j + 1
                        title = s.find_elements_by_class_name('other-sites__snippet-title')[0]
                        atittle = title.find_elements_by_tag_name('a')[0]
                        title = atittle.get_attribute('innerText')
                        url = atittle.get_attribute('href')
                        domain = s.find_elements_by_class_name('other-sites__snippet-site')[0]
                        domain = domain.find_elements_by_tag_name('a')[0].get_attribute('innerText')
                        info = {}
                        info["originUrl"] = link
                        info["title"] = title
                        info["url"] = url
                        info["domain"] = domain
                        if verbose:
                            print("-----------------")
                            print(info)
                        out.append(info)
                        try:
                            urllib.request.urlretrieve(link, name)
                        except:
                            print("Failed when downloading photo " + str(j))


        except Exception as e:
            print(e)

    return out


def deletedImage(hashimage, token):
    headers = {'Authorization': 'Client-ID ' + token}
    req = requests.delete(url="https://api.imgur.com/3/image/" + hashimage, headers=headers)
    if req.status_code == requests.codes.ok:
        return True
    else:
        return False


def yandex(image, token, verbose):
    if not os.path.isdir("data/yandex"):
        os.mkdir("data/yandex");
    image_url = image
    image_delete = ""
    results = {}
    url = re.findall('http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+] |[!*\(\), ]|(?:%[0-9a-fA-F][0-9a-fA-F]))+', image)
    if not url:
        try:
            f = open(image, "rb")
        except FileNotFoundError as e:
            print("Image not found: " + image)
            return []
        # sys.exit(-1)
        image_data = f.read()
        b64_image = base64.standard_b64encode(image_data)
        client_id = token
        headers = {'Authorization': 'Client-ID ' + token}
        data = {'image': b64_image, 'title': 'test'}
        try:
            request = requests.post(url="https://api.imgur.com/3/upload.json", data=data, headers=headers)
            if request.status_code == requests.codes.ok:
                image_url = request.json()['data']['link']
                image_delete = request.json()['data']['deletehash']
                print("Image upload to imgur: " + image_url)
        except Exception as e:
            print(e)
            sys.exit(-1)

    proxy = crawlProxy()
    if proxy is not None:
        print(proxy)
        chrome_options = webdriver.ChromeOptions()
        chrome_options.add_argument("--headless")
        chrome_options.add_argument('--proxy-server=%s' % proxy)
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_path = './chromedriver'
        driver = webdriver.Chrome(chrome_path, options=chrome_options)
        url_final = "https://yandex.ru/images/search?rpt=imageview&url=" + image_url + "&rpt=imagelike"
        driver.get(url_final)
        driver.implicitly_wait(50)
        time.sleep(3)
        captcha = isCaptcha(driver)
        if captcha == True:
            driver.close()
        else:
            now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            images = searchImages(driver, now, verbose)
            if not images:
                print('No images.')
                driver.close()
            path = os.path.join('data/yandex', str(now) + '_yandex_data.json')
            with open(path, 'w+') as outfile:
                json.dump(images, outfile)

        if not token == None:
            if deletedImage(image_delete, token):
                print("Image deleted")
            else:
                print("Problem when deleted image from imgur")

        print("Results Yandex in: " + str(path))
        results['results'] = str(path)
    else:
        print('Yandex is blocked')

    return results
