import asyncio
import aiohttp
import aiofiles
import requests
from lxml import etree
import os


headers = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
}


async def download_one(url, file_path): # 因为发送请求类似io操作，所以前面加async
    print("开始下载")
    async with aiohttp.ClientSession() as session:
        print(url)
        async with session.get(url, headers = headers) as resp:
            page_source = await resp.text(encoding = "UTF-8")
            tree = etree.HTML(page_source)
            content = tree.xpath("//div[@class = 'content']//p//text()")
            content = "\n".join(content)

            async with aiofiles.open(file_path, mode = 'w', encoding = 'utf-8') as f:
                await f.write(content)
    print("下载了一篇")




async def download_chapter(chapter_list):
    tasks = []
    for chapter in chapter_list:
        juan_name = chapter['juan']
        chapter_name = chapter['chapter']
        chapter_url = chapter['url']
        if not os.path.exists(juan_name):
            os.mkdir(juan_name)   # 创好文件夹，那就要循环下载了，因为有很多io操作，所以这个函数也要夹async，并且再来一个函数做
                                  # 遍历下载txt
        '''
        需求是一卷一个文件夹，文件夹里的文件格式是  卷明/章节名.txt
        所以download_one还需要多一个参数，filepath
        '''
        file_path = f"{juan_name}/{chapter_name}.txt"
        t = asyncio.create_task(download_one(chapter_url, file_path))
        tasks.append(t)
    await asyncio.wait(tasks)



def get_chapter_info(url):
    main_page_source = requests.get(url, headers = headers)
    main_page_source.encoding = "UTF-8"
    tree = etree.HTML(main_page_source.text)
    divs = tree.xpath("//div[@class='mulu']")

    result = []
    for div in divs: # 从返回的tr列表中拿到卷名
        trs = div.xpath(".//table/tr")
        juan_name = "".join(trs[0].xpath(".//h2/a/text()")).strip().replace('：','_')
        for tr in trs[1:]: # 先对tr列表切片（去掉卷名），遍历拿到td列表，里面包含了href和章节名
            tds = tr.xpath("./td")
            for td in tds: # 遍历td列表，拿到章节名和href
                chapter_name = "".join(td.xpath(".//text()")).strip().replace(" ", '_')
                chapter_url = "".join(td.xpath(".//@href"))
                dic = {"juan":juan_name, "chapter":chapter_name, "url":chapter_url}
                result.append(dic)
    return result



def main(): # 把之前定义的所有方法封装在main（）里面，统一调度
    chapter_list = get_chapter_info("https://www.mingchaonaxieshier.com/") #拿到章节信息，接下来就要下载
    download_chapter(chapter_list)
    asyncio.run(download_chapter(chapter_list))



if __name__ == '__main__':
    main()