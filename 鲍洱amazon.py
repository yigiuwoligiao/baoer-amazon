import requests
import time
from lxml import etree
import random
import hashlib

requests.packages.urllib3.disable_warnings()


# 动态转发
def down(url):
    '''
    使用讯代理下载指定的页面
    :param url:
    :return:
    '''
    orderno = "xxxxxxx"  # 订单号
    secret = "xxxxxxxxxxxxxxx"  # 秘钥
    ip = "forward.xdaili.cn"
    port = "80"
    ip_port = ip + ":" + port
    nums = 1
    while nums <= 3:
        # 生成签名参数sign
        timestamp = str(int(time.time()))  # 10位的时间戳
        string = "orderno=" + orderno + "," + "secret=" + secret + "," + "timestamp=" + timestamp
        string = string.encode()
        md5_string = hashlib.md5(string).hexdigest()
        sign = md5_string.upper()
        # auth验证信息
        auth = "sign=" + sign + "&" + "orderno=" + orderno + "&" + "timestamp=" + timestamp
        # 代理ip
        proxy = {"http": "http://" + ip_port, "https": "https://" + ip_port}
        # 请求头
        headers = {"Proxy-Authorization": auth,
                   "User-Agent": "Mozilla/5.0 (Windows NT 6.1; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/73.0.3683.75 Safari/537.36"
                   }
        try:
            # 通过代理IP进行请求
            response = requests.get(url, headers=headers, proxies=proxy, verify=False, allow_redirects=False)
            if response.status_code == 200:
                return response
            else:
                nums += 1
        except Exception as e:
            nums += 1
    return None


def get_html(url):
    '''
    首页解析
    :param url:
    :return:
    '''

    response = down(url)
    html = response.text
    # print('状态码', response.status_code)

    # 1) 抓取Best Sellers栏目下所有产品分类
    html = etree.HTML(html)
    # 链接
    classify_url = html.xpath('//ul[@id="zg_browseRoot"]/ul/li/a/@href')

    classify_url_list = []
    for i in classify_url:
        classify_url_list.append(i)
    # print(len(classify_url_list))
    return classify_url_list


def get_top100(classify_url_list):
    # 2) 从1)中随机选取一个分类，抓取该分类下top100产品列表
    headers = {
        'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/83.0.4103.106 Safari/537.36'
    }
    url2 = random.choice(classify_url_list)
    url2 = url2.rsplit('/', 2)[0]
    # print('原本的url',url2)
    url2 = url2 + '/ref=zg_bs_pg_2?_encoding=UTF8&pg='
    # print('拼接的',url2)
    shop_ls = []
    for pg in range(1, 3):
        response = requests.get(url2 + str(pg), headers=headers, verify=False)
        # print('进入循环后的',url2)
        html = response.text
        html = etree.HTML(html)
        ls = html.xpath('//ol[@id="zg-ordered-list"]/li')
        # top100商品链接

        for i in ls:
            a_num = i.xpath('.//span[@class="zg-badge-text"]/text()')
            # print('序号', a_num)
            a_url = i.xpath('.//span[@class="aok-inline-block zg-item"]/a[1]/@href')
            # print('链接',a_url)
            shop_ls.append(a_url)
    return shop_ls


def get_parser(shop_ls):
    # 3) 从2)中随机选取一个产品，抓取该产品listing内容、评论、星级、售价等数据，也可自由发挥抓取其它数据。
    # 要求： 引用python包请注明版本号，结果与实现代码请一并发送。
    save_ls = []
    detail_url = 'https://www.amazon.com' + random.choice(shop_ls)[0]
    print('随机选择的商品商品链接', detail_url)
    response = down(detail_url)
    html = etree.HTML(response.text)

    try:
        title = html.xpath('//span[@id="productTitle"]/text()')[0].strip()
        print('商品名:', title)
    except Exception as e:
        title = html.xpath('.//span[@class="a-size-large a-text-bold"]/text()')[0]
        print('商品名:', title)
    try:
        price = html.xpath('//span[@id="priceblock_ourprice"]/text()')
        if len(price) > 0:
            price = price[0]
            print('价格:', price)
        else:
            price = "没标价"
            print('价格:', price)
    except Exception as e:
        # a-size-base a-color-price
        price = html.xpath('//span[@id="a-size-base a-color-price"]/text()')
        if len(price) > 0:
            price = price[0]
            print('价格:', price)
        else:
            price = "没标价"
            print('价格:', price)
    pinglun_ls = html.xpath('//div[@class="a-section review-views celwidget"]/div')
    for i in pinglun_ls:
        name = i.xpath('.//div[@class="a-profile-content"]/span/text()')[0]
        print('评论人姓名:', name)
        content = i.xpath(
            './/div[@class="a-expander-content reviewText review-text-content a-expander-partial-collapse-content"]/span/text()')
        if len(content) > 0:
            content = content[0]
            print('评论内容:', content)
        else:
            content = '当前没人评论'
            print('评论内容:', content)

        star = i.xpath('.//i[contains(@class,"a-icon a-icon-star")]/span/text()')[0]
        star = star.split(' ')[0]
        print('评价的星星:', star)
        print('=' * 200)
        save_ls = [detail_url, '\r', title, '\r', price, '\r', name, '\r', content, '\r', star, '\r']
    return save_ls


def write_txt(save_ls):
    '''
    存txt,因为传进来的save_ls是列表套列表,为了存储时每条数据能换行,所以写个循环
    :param save_ls:
    :return:
    '''
    try:
        with open('./amazon.txt', 'a+', encoding='utf-8')as f:
            for i in save_ls:
                for j in i:
                    f.write(str(j))
            print('写入完成')
    except Exception as e:
        print(e)


if __name__ == '__main__':
    url = 'https://www.amazon.com/gp/bestsellers/?ref_=nav_cs_bestsellers'
    classify_url_list = get_html(url)
    shop_ls = get_top100(classify_url_list)
    save_ls = get_parser(shop_ls)
    write_txt(save_ls)
