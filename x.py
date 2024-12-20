import requests
import re
import json
import re

from urllib.parse import urlparse
from dataclasses import dataclass
from typing import Optional, Tuple, List


DEFAULT_USER_AGENT = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36'


def milliseconds_to_seconds(milliseconds: int) -> int:
    return milliseconds // 1000


def download_video(url: str, save_path: str) -> bool:
    try:
        response = requests.get(url, stream=True)
        response.raise_for_status()
        
        with open(save_path, 'wb') as video_file:
            for chunk in response.iter_content(chunk_size=8192):
                video_file.write(chunk)
    except Exception as e:
        return False
    
    return True


def get_username_from_url(url):
    parsed_url = urlparse(url)
    path = parsed_url.path
    username = path.strip("/")
    return username


@dataclass
class VideoInfo:
    url: str
    duration_millis: int


class X:
    def __init__(self, token: str, cookie_str: str, proxy: Optional[str] = None):
        self._request = requests.Session()

        self._request.headers.update({
            'authorization': token,
            'cookie': cookie_str,
            'user-agent': DEFAULT_USER_AGENT
        })

        csrf_token = self._get_csrf_token()
        self._request.headers.update({
            'x-csrf-token': csrf_token
        })

        if proxy:
            self._request.proxies = {
                'http': f'http://{proxy}',
                'https': f'http://{proxy}'
            }

        self._base_url = 'https://x.com/i/api/graphql'
        self._timeout = 30

    def get_video_urls(self, user_id: str, cursor: Optional[str] = None) -> Tuple[List[VideoInfo], Optional[str]]:
        variables = {
            "userId": user_id,
            "count": 20,
            "includePromotedContent": True,
            "withQuickPromoteEligibilityTweetFields": True,
            "withVoice": True,
            "withV2Timeline": True
        }
        
        if cursor:
            variables.update({
                'cursor': cursor
            })

        params = {
            'variables': json.dumps(variables),
            'features': '{"rweb_tipjar_consumption_enabled":true,"responsive_web_graphql_exclude_directive_enabled":true,"verified_phone_label_enabled":false,"creator_subscriptions_tweet_preview_api_enabled":true,"responsive_web_graphql_timeline_navigation_enabled":true,"responsive_web_graphql_skip_user_profile_image_extensions_enabled":false,"communities_web_enable_tweet_community_results_fetch":true,"c9s_tweet_anatomy_moderator_badge_enabled":true,"articles_preview_enabled":true,"responsive_web_edit_tweet_api_enabled":true,"graphql_is_translatable_rweb_tweet_is_translatable_enabled":true,"view_counts_everywhere_api_enabled":true,"longform_notetweets_consumption_enabled":true,"responsive_web_twitter_article_tweet_consumption_enabled":true,"tweet_awards_web_tipping_enabled":false,"creator_subscriptions_quote_tweet_preview_enabled":false,"freedom_of_speech_not_reach_fetch_enabled":true,"standardized_nudges_misinfo":true,"tweet_with_visibility_results_prefer_gql_limited_actions_policy_enabled":true,"rweb_video_timestamps_enabled":true,"longform_notetweets_rich_text_read_enabled":true,"longform_notetweets_inline_media_enabled":true,"responsive_web_enhance_cards_enabled":false}',
            'fieldToggles': '{"withArticlePlainText":false}'
        }
        response = self._request.get(f'{self._base_url}/Tg82Ez_kxVaJf7OPbUdbCg/UserTweets', params=params, timeout=self._timeout)
        
        videos = []
        cursor = None

        try:
            data = response.json()
            entries =  data['data']['user']['result']['timeline_v2']['timeline']['instructions'][-1]['entries']

            string_value = re.findall('"string_value": "({.*?})",', json.dumps(data))
            for value in string_value:
                value = json.loads(value.replace('\\', ''))
                media_entities: dict = value['media_entities']

                for key in media_entities.keys():
                    if 'video_info' in media_entities[key]:
                        video_info = media_entities[key]['video_info']
                        duration_millis = video_info['duration_millis']
                        video_url = video_info['variants'][0]['url']

                        if '.mp4' in video_url:
                            videos.append(VideoInfo(video_url, duration_millis))
                            
            # for item in entries[:-2]:
            #     content = item['content']
            #     if 'itemContent' in content:
            #         entities = content['itemContent']['tweet_results']['result']['legacy']['entities']
            #         if 'media'in entities:
            #             entities = entities['media'][-1]
            #             if 'video_info' in entities:
            #                 video_info = entities['video_info']
            #                 duration_millis = video_info['duration_millis']
            #                 video_url = video_info['variants'][-1]['url']

            #                 videos.append(VideoInfo(video_url, duration_millis))

            cursor = entries[-1]['content']['value']
        except Exception as ex:
            print(response.text.strip())
            print(ex)

        return videos, cursor

    def get_rest_id(self, screen_name: str) -> Optional[str]:
        params = {
            'variables': json.dumps({"screen_name":screen_name}),
            'features': '{"hidden_profile_subscriptions_enabled":true,"rweb_tipjar_consumption_enabled":true,"responsive_web_graphql_exclude_directive_enabled":true,"verified_phone_label_enabled":false,"subscriptions_verification_info_is_identity_verified_enabled":true,"subscriptions_verification_info_verified_since_enabled":true,"highlights_tweets_tab_ui_enabled":true,"responsive_web_twitter_article_notes_tab_enabled":true,"subscriptions_feature_can_gift_premium":true,"creator_subscriptions_tweet_preview_api_enabled":true,"responsive_web_graphql_skip_user_profile_image_extensions_enabled":false,"responsive_web_graphql_timeline_navigation_enabled":true,"communities_web_enable_tweet_community_results_fetch":true,"c9s_tweet_anatomy_moderator_badge_enabled":true,"articles_preview_enabled":true,"tweetypie_unmention_optimization_enabled":true,"responsive_web_edit_tweet_api_enabled":true,"graphql_is_translatable_rweb_tweet_is_translatable_enabled":true,"view_counts_everywhere_api_enabled":true,"longform_notetweets_consumption_enabled":true,"responsive_web_twitter_article_tweet_consumption_enabled":true,"tweet_awards_web_tipping_enabled":false,"creator_subscriptions_quote_tweet_preview_enabled":false,"freedom_of_speech_not_reach_fetch_enabled":true,"standardized_nudges_misinfo":true,"tweet_with_visibility_results_prefer_gql_limited_actions_policy_enabled":true,"rweb_video_timestamps_enabled":true,"longform_notetweets_rich_text_read_enabled":true,"longform_notetweets_inline_media_enabled":true,"responsive_web_enhance_cards_enabled":false}',
            'fieldToggles': '{"withAuxiliaryUserLabels":false}'
        }
        response = self._request.get(f'{self._base_url}/laYnJPCAcVo0o6pzcnlVxQ/UserByScreenName',
                                     params=params,
                                     timeout=self._timeout)
        rest_id = None

        try:
            data = response.json()
            rest_id = data['data']['user']['result']['rest_id']
        except Exception as ex:
            print(response.text.strip())
            print(ex)

        return rest_id

    def _get_csrf_token(self) -> str:
        result = re.findall('ct0=(.*?);', self._request.headers['cookie'])
        return result[-1]