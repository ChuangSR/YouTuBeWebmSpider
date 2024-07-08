from concurrent.futures import ThreadPoolExecutor
from threading import Thread
from scrapy.crawler import CrawlerProcess
from scrapy.utils.project import get_project_settings
from youtube.dao.SqliteDao import SqliteDao

from pytube import YouTube

from youtube.utils.util import Util
import os
import platform
import ctypes


def get_free_space_status(folder,reserved_size):
    """
    获取磁盘剩余空间
    :param folder: 磁盘路径 例如 D:\\
    :return: 剩余空间 单位 G
    """
    if platform.system() == 'Windows':
        free_bytes = ctypes.c_ulonglong(0)
        ctypes.windll.kernel32.GetDiskFreeSpaceExW(ctypes.c_wchar_p(folder), None, None, ctypes.pointer(free_bytes))
        return free_bytes.value / 1024 / 1024 // 1024 > reserved_size
    else:
        st = os.statvfs(folder)
        return st.f_bavail * st.f_frsize / 1024 // 1024 > reserved_size


def download(root_path, database_name, save_path, max_workers,reserved_size):
    if not get_free_space_status(root_path,reserved_size):
        print("空间不足")
        return
    path = f"{root_path}/{database_name}"
    dao = SqliteDao(path=path)
    results = dao.select_all()
    download_thread = Thread(target=start_download_thread, args=(save_path, max_workers,results,reserved_size,))
    download_thread.start()
    download_thread.join()

    for result in results:
        if os.path.exists(Util.get_path(save_path,f"{result[3]}.webm")):
            dao.update(result[0])
    dao.close()


def start_download_thread(output_path, max_workers,results,reserved_size):
    threadPool = ThreadPoolExecutor(max_workers=max_workers)
    for result in results:
        if not get_free_space_status(output_path, reserved_size):
            print("空间不足")
            break
        threadPool.submit(download_thread, result, output_path,reserved_size)
    threadPool.shutdown(wait=True)
def download_thread(result: tuple, output_path,reserved_size):
    if not get_free_space_status(output_path,reserved_size):
        print("空间不足")
        return
    videoId = result[1]
    name = result[3]
    print(f"{name}开始下载！")
    try:
        yt = YouTube(f"https://youtube.com/watch?v={videoId}")
        (yt.streams.filter(only_audio=True, mime_type="audio/webm").
         order_by("abr").desc().first().download(output_path=output_path, filename=f"{name}.webm"))
        print(f"{name}下载完成！")
    except Exception as e:
        print(f"{name}下载失败！")
        print(e)
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
    return None


def run(save_path, max_workers,reserved_size):
    root_path = "./resource"
    if not os.path.exists(root_path):
        os.makedirs(root_path)
    else:
        dirs = os.listdir(root_path)
        for i in dirs:
            print(i)
            download(root_path, i,
                     Util.get_path(save_path, Util.replace_name(i.split("@")[-1])),
                     max_workers,reserved_size)

    # 获取id
    user = get_user()
    while user:
        database_name = run_spider(user)
        download(root_path, database_name,
                 Util.get_path(save_path, Util.replace_name(database_name.split("@")[-1])),
                 max_workers,reserved_size)
        user = get_user()

if __name__ == "__main__":
    # 保存文件的路径
    save_path = "./webm"
    # 下载的线程数目
    max_workers = 16
    #保留的空间，单位G
    reserved_size = 0
    run(save_path, max_workers,reserved_size)
