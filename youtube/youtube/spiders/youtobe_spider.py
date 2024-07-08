import base64
import json
from typing import Iterable, Union

import scrapy
from scrapy import Request, Spider
from fake_useragent import UserAgent
from twisted.internet.defer import Deferred

from youtube.dao.SqliteDao import SqliteDao
from youtube.items import YoutubeItem


class YoutobeSpiderSpider(scrapy.Spider):
    name = "youtobe_spider"
    allowed_domains = ["youtube.com"]
    ua = UserAgent(os=["windows"])
    def start_requests(self) -> Iterable[Request]:
        self.dao = SqliteDao(name=self.settings.name)
        yield scrapy.Request(url=f"https://www.youtube.com/{self.settings.name}", headers=self._get_root_headers())

    def parse(self, response):
        texts = response.xpath("//script/text()")
        for text in texts:
            text = str(text)
            if "var ytInitialData = {\"responseContext\"" in text:
                text_list = text.split("trackingParams")
                for i in text_list:
                    if "browseEndpoint" in i and "\"title\":\"视频\",\"" in i:
                        i = i.split("\"browseEndpoint\":")[-1].split("},\"title")[0]
                        data_json = json.loads(i)
                        if data_json:
                            browseId = data_json["browseId"]
                            params = data_json["params"]
                            print(self.settings.name)
                            print(data_json)
                            yield self._get_root_json_request(browseId=browseId, params=params)
                break
    def parse_browse(self,response):
        json_data = json.loads(response.text)
        contents = self._get_contents(json_data)
        if not contents:
            return
        token = None
        try:
            token = contents[-1]["continuationItemRenderer"]["continuationEndpoint"]["continuationCommand"]["token"]
        except Exception as e:
            print(e)
        if token:
            del contents[-1]
            yield self._get_root_json_request(token=token)

        for i in contents:
            item = YoutubeItem()
            videoRenderer = i["richItemRenderer"]["content"]["videoRenderer"]
            item["videoId"] = videoRenderer["videoId"]
            item["title"] = videoRenderer["title"]["runs"][0]["text"]
            item["lengthText"] = videoRenderer["lengthText"]["simpleText"]
            print(item)
            title: str = item["title"]
            item["title"] = base64.b64encode(title.encode("utf-8")).decode("utf-8")
            yield item
    def _get_contents(self,json_data):
        contents = None
        try:
            contents = (json_data["contents"]["twoColumnBrowseResultsRenderer"]["tabs"]
                    [1]["tabRenderer"]["content"]["richGridRenderer"]["contents"])
        except Exception as e:
            print(e)
        if contents:
            return contents
        try:
            contents = (json_data["onResponseReceivedActions"][0]["appendContinuationItemsAction"]
            ["continuationItems"])
        except Exception as e:
            print(e)
        return contents
    def _get_root_headers(self):
        return {
            'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
            'accept-language': 'zh-CN,zh;q=0.9,en;q=0.8,en-GB;q=0.7,en-US;q=0.6',
            'cache-control': 'no-cache',
            'pragma': 'no-cache',
            'priority': 'u=0, i',
            'sec-ch-ua': '"Not/A)Brand";v="8", "Chromium";v="126", "Microsoft Edge";v="126"',
            'sec-ch-ua-arch': '"x86"',
            'sec-ch-ua-bitness': '"64"',
            'sec-ch-ua-full-version-list': '"Not/A)Brand";v="8.0.0.0", "Chromium";v="126.0.6478.127", "Microsoft Edge";v="126.0.2592.81"',
            'sec-ch-ua-mobile': '?0',
            'sec-ch-ua-model': '""',
            'sec-ch-ua-platform': '"Windows"',
            'sec-ch-ua-platform-version': '"14.0.0"',
            'sec-ch-ua-wow64': '?0',
            'sec-fetch-dest': 'document',
            'sec-fetch-mode': 'navigate',
            'sec-fetch-site': 'same-origin',
            'sec-fetch-user': '?1',
            'service-worker-navigation-preload': 'true',
            'upgrade-insecure-requests': '1',
            'user-agent': self.ua.random
        }

    def _get_root_josn_header(self,ua):
        return {
            'accept': '*/*',
            'accept-language': 'zh-CN,zh;q=0.9,en;q=0.8,en-GB;q=0.7,en-US;q=0.6',
            'cache-control': 'no-cache',
            'content-type': 'application/json',
            'origin': 'https://www.youtube.com',
            'pragma': 'no-cache',
            'priority': 'u=1, i',
            'referer': 'https://www.youtube.com/',
            'sec-ch-ua': '"Not/A)Brand";v="8", "Chromium";v="126", "Google Chrome";v="126"',
            'sec-ch-ua-arch': '"x86"',
            'sec-ch-ua-bitness': '"64"',
            'sec-ch-ua-form-factors': '"Desktop"',
            'sec-ch-ua-full-version': '"126.0.6478.114"',
            'sec-ch-ua-full-version-list': '"Not/A)Brand";v="8.0.0.0", "Chromium";v="126.0.6478.114", "Google Chrome";v="126.0.6478.114"',
            'sec-ch-ua-mobile': '?0',
            'sec-ch-ua-model': '""',
            'sec-ch-ua-platform': '"Windows"',
            'sec-ch-ua-platform-version': '"10.0.0"',
            'sec-ch-ua-wow64': '?0',
            'sec-fetch-dest': 'empty',
            'sec-fetch-mode': 'same-origin',
            'sec-fetch-site': 'same-origin',
            'user-agent': ua,
            'x-goog-visitor-id': 'CgtWM0l3NnlmN3U3byiUzf-zBjIKCgJISxIEGgAgEg%3D%3D',
            'x-youtube-bootstrap-logged-in': 'false',
            'x-youtube-client-name': '1',
            'x-youtube-client-version': '2.20240628.01.00',
        }
    def _get_root_json_request(self, browseId=None, params=None, token=None):
        ua = self.ua.random
        json_data = {
            'context': {
                'client': {
                    'hl': 'zh-CN',
                    'gl': 'HK',
                    'remoteHost': '',
                    'deviceMake': '',
                    'deviceModel': '',
                    'visitorData': '',
                    'userAgent': ua,
                    'clientName': 'WEB',
                    'clientVersion': '2.20240628.01.00',
                    'osName': 'Windows',
                    'osVersion': '10.0',
                    'originalUrl': 'https://www.youtube.com/',
                    'platform': 'DESKTOP',
                    'clientFormFactor': 'UNKNOWN_FORM_FACTOR',
                    'configInfo': {},
                    'userInterfaceTheme': 'USER_INTERFACE_THEME_LIGHT',
                    'browserName': 'Chrome',
                    'browserVersion': '126.0.0.0',
                    'acceptHeader': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
                    'deviceExperimentId': 'ChxOek00TlRnM05UUXpOelkxTURVM016YzNNQT09EJTN_7MGGJTN_7MG',
                    'screenWidthPoints': 1204,
                    'screenHeightPoints': 1332,
                    'screenPixelDensity': 1,
                    'screenDensityFloat': 1,
                    'utcOffsetMinutes': 480,
                    'connectionType': 'CONN_CELLULAR_4G',
                    'memoryTotalKbytes': '8000000',
                    'mainAppWebInfo': {
                        'graftUrl': 'https://www.youtube.com/',
                        'pwaInstallabilityStatus': 'PWA_INSTALLABILITY_STATUS_CAN_BE_INSTALLED',
                        'webDisplayMode': 'WEB_DISPLAY_MODE_BROWSER',
                        'isWebNativeShareAvailable': True,
                    },
                    'timeZone': 'Asia/Shanghai',
                },
                'user': {
                    'lockedSafetyMode': False,
                },
                'request': {
                    'useSsl': True,
                    'internalExperimentFlags': [],
                    'consistencyTokenJars': [],
                },
                'clickTracking': {
                    'clickTrackingParams': 'CBEQ8eIEIhMIm_OHp9KAhwMV5waDAx2CQA8d',
                },
                'adSignalsInfo': {},
            }
        }
        if token:
            json_data["continuation"] = token
        else:
            json_data['browseId'] = browseId
            json_data['params'] = params
        return scrapy.http.JsonRequest(url="https://www.youtube.com/youtubei/v1/browse?prettyPrint=false",
                                       headers=self._get_root_josn_header(ua),data=json_data,callback=self.parse_browse)

    @staticmethod
    def close(spider: Spider, reason: str) -> Union[Deferred, None]:
        spider.dao.close()
        return super().close(spider, reason)

