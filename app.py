import x
import json

token = 'Bearer AAAAAAAAAAAAAAAAAAAAANRILgAAAAAAnNwIzUejRCOuH5E6I8xnZz4puTs%3D1Zv7ttfk8LF81IUq16cHjhLTvJu4FA33AGWWjCpTnA'
cookie = 'guest_id=173184390879426294; night_mode=2; guest_id_marketing=v1%3A173184390879426294; guest_id_ads=v1%3A173184390879426294; gt=1858114146421837951; g_state={"i_l":0}; kdt=r0B1aqiIggZhOrHREPBdRArN5C4AlIcUluHS2QYL; auth_token=64e85a79a3c01012bbe1612b2cdf9bb226b39444; ct0=1624b82aaf1b6a337de41ec28ef66d19edaf50858934e793cc5487bf0f780f7e61670288c71f08ea574bddd157dbf950800b168196cc092fffb47b57ebffb831a263e9e07eac18b6d0be7025849c5220; att=1-sPMIJRsgookNSt87Dl5Jm7ZtXSaoHwNDFTXTLsnQ; lang=en; twid=u%3D1858077356851896320; personalization_id="v1_kBWPQP+zBk5QWIVN0o5Sqg=="'
api = x.X(token, cookie)

user_id = api.get_rest_id('ThuanCapital')

with open('log.json', 'w', encoding='utf-8') as file:
    media = api.get_media(user_id)
    json.dump(media, file, indent=4)
