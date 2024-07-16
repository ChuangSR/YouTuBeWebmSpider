from concurrent.futures import ThreadPoolExecutor
from threading import Thread
from scrapy.crawler import CrawlerProcess
from scrapy.utils.project import get_project_settings
from youtube.dao.SqliteDao import SqliteDao

from pytube import YouTube

from youtube.utils.util import Util
import os
import yt_dlp

def download(root_path, database_name, save_path, max_workers):
    path = f"{root_path}/{database_name}"
    dao = SqliteDao(path=path)
    results = dao.select_all()
    download_thread = Thread(target=start_download_thread, args=(save_path, max_workers, results,))
    download_thread.start()
    download_thread.join()

    for result in results:
        if os.path.exists(Util.get_path(save_path, f"{result[3]}.webm")):
            dao.update(result[0])
    dao.close()


def start_download_thread(output_path, max_workers, results):
    threadPool = ThreadPoolExecutor(max_workers=max_workers)
    for result in results:
        threadPool.submit(download_thread, result, output_path)
    threadPool.shutdown(wait=True)


def download_thread(result: tuple, output_path):
    videoId = result[1]
    name = result[3]
    print(f"{name}开始下载！")
    yt_dlp_download(videoId,output_path)
def pytube_download(name,videoId,output_path):
    yt = YouTube(f"https://youtube.com/watch?v={videoId}")
    (yt.streams.filter(only_audio=True, mime_type="audio/webm").
     order_by("abr").desc().first().download(output_path=output_path, filename=f"{name}.webm"))

def yt_dlp_download(videoId,name,output_path):
    def format_selector(ctx):
        formats = ctx.get('formats')
        webm = {}
        for f in formats:
            ext_type = f.get("audio_ext")
            abr = f.get("format_id")
            size = f.get("filesize")
            if ext_type == "webm" and "drc" not in abr:
                if webm.get("size", 0) < size:
                    webm = f
        yield {
            'format_id': f"{webm['format_id']}",
            'ext': webm['ext'],
            'requested_formats': [webm],
            # Must be + separated list of protocols
            'protocol': f"{webm['protocol']}"
        }

    ydl_opts = {
        'format': format_selector,
        "paths": {
            "home": output_path
        },
        "outtmpl": {
            "default": name
        }
    }

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        ydl.download(f"https://youtube.com/watch?v={videoId}")

def run_spider(name):
    setting = get_project_settings()
    setting.name = name
    crawler = CrawlerProcess(setting)
    crawler.crawl('youtobe_spider')
    crawler.start()
    return f"database_{Util.replace_name(name)}.db"


# 获取用户id的方法
def get_user():
    # 这个是你需要实现的
    # 用户名为@xxxx的形式
    return "@ownwid"


def run(save_path, max_workers):
    root_path = "./resource"
    if not os.path.exists(root_path):
        os.makedirs(root_path)
    else:
        dirs = os.listdir(root_path)
        for i in dirs:
            print(i)
            download(root_path, i,
                     Util.get_path(save_path, Util.replace_name(i.split("@")[-1])),
                     max_workers)

    # 获取id
    user = get_user()
    while user:
        database_name = run_spider(user)
        download(root_path, database_name,
                 Util.get_path(save_path, Util.replace_name(database_name.split("@")[-1])),
                 max_workers)
        user = None


if __name__ == "__main__":
    # 保存文件的路径
    save_path = "./webm"
    # 下载的线程数目
    max_workers = 16
    run(save_path, max_workers)
    # result = [0, 0, 0, 0]
    # result[1] = ""
    # result[3] = "temp"
    # # download_thread(tuple(result),save_path)
    #
    # yt = YouTube(f"https://youtube.com/watch?v=Uq9pm2klKUc")
    # (yt.streams.filter(only_audio=True, mime_type="audio/webm").
    #  order_by("abr").desc().first().download(output_path="./webm", filename="temp.webm"))
