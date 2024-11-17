import requests
import re
import json

from urllib.parse import urlparse
from dataclasses import dataclass
from typing import Optional, Tuple, List


DEFAULT_USER_AGENT = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36'


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
    def __init__(self, token: str, cookie_str: str):
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

        self._base_url = 'https://x.com/i/api/graphql'

    def get_media(self, user_id: str, cursor: Optional[str] = None) -> Tuple[List[VideoInfo], str]:
        variables = {
            "userId": user_id,
            "count": 20,
            "includePromotedContent": False,
            "withClientEventToken": False,
            "withBirdwatchNotes": False,
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
        response = self._request.get(f'{self._base_url}/HaouMjBviBKKTYZGV_9qtg/UserMedia', params=params)
        data = response.json()

        entries =  data['data']['user']['result']['timeline_v2']['timeline']['instructions'][-1]['entries']
        videos = []
        
        if len(entries) > 2:
            items = entries[0]['content']['items']

            for item in items:
                entities = item['item']['itemContent']['tweet_results']['result']['legacy']['entities']
                if 'media'in entities:
                    entities = entities['media'][-1]
                    if 'video_info' in entities:
                        video_info = entities['video_info']
                        duration_millis = video_info['duration_millis']
                        video_url = video_info['variants'][-1]['url']

                        videos.append(VideoInfo(video_url, duration_millis))

        return videos, entries[-1]['content']['value']

    def get_rest_id(self, screen_name: str) -> str:
        params = {
            'variables': json.dumps({"screen_name":screen_name}),
            'features': '{"hidden_profile_subscriptions_enabled":true,"rweb_tipjar_consumption_enabled":true,"responsive_web_graphql_exclude_directive_enabled":true,"verified_phone_label_enabled":false,"subscriptions_verification_info_is_identity_verified_enabled":true,"subscriptions_verification_info_verified_since_enabled":true,"highlights_tweets_tab_ui_enabled":true,"responsive_web_twitter_article_notes_tab_enabled":true,"subscriptions_feature_can_gift_premium":true,"creator_subscriptions_tweet_preview_api_enabled":true,"responsive_web_graphql_skip_user_profile_image_extensions_enabled":false,"responsive_web_graphql_timeline_navigation_enabled":true,"communities_web_enable_tweet_community_results_fetch":true,"c9s_tweet_anatomy_moderator_badge_enabled":true,"articles_preview_enabled":true,"tweetypie_unmention_optimization_enabled":true,"responsive_web_edit_tweet_api_enabled":true,"graphql_is_translatable_rweb_tweet_is_translatable_enabled":true,"view_counts_everywhere_api_enabled":true,"longform_notetweets_consumption_enabled":true,"responsive_web_twitter_article_tweet_consumption_enabled":true,"tweet_awards_web_tipping_enabled":false,"creator_subscriptions_quote_tweet_preview_enabled":false,"freedom_of_speech_not_reach_fetch_enabled":true,"standardized_nudges_misinfo":true,"tweet_with_visibility_results_prefer_gql_limited_actions_policy_enabled":true,"rweb_video_timestamps_enabled":true,"longform_notetweets_rich_text_read_enabled":true,"longform_notetweets_inline_media_enabled":true,"responsive_web_enhance_cards_enabled":false}',
            'fieldToggles': '{"withAuxiliaryUserLabels":false}'
        }
        response = self._request.get(f'{self._base_url}/laYnJPCAcVo0o6pzcnlVxQ/UserByScreenName',
                                     params=params)
        data = response.json()
        return data['data']['user']['result']['rest_id']

    def _get_csrf_token(self) -> str:
        result = re.findall('ct0=(.*?);', self._request.headers['cookie'])
        return result[-1]