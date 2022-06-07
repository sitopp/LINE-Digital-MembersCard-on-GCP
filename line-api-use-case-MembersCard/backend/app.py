import os
import json
import math
import random
import datetime
import requests
from decimal import Decimal
from dateutil.tz import gettz
from dateutil.relativedelta import relativedelta
import logging
import send_message
from members_card_user_info import MembersCardUserInfo
from common import utils

# 環境変数の宣言
LOGGER_LEVEL = os.getenv('LOGGER_LEVEL')
LIFF_CHANNEL_ID = os.getenv('LIFF_CHANNEL_ID', None)
CHANNEL_ACCESS_TOKEN = os.getenv('CHANNEL_ACCESS_TOKEN')

# ログ出力の設定
logger = logging.getLogger()
if LOGGER_LEVEL == 'DEBUG':
    logger.setLevel(logging.DEBUG)
else:
    logger.setLevel(logging.INFO)

# テーブル操作クラスの初期化
user_info_table_controller = MembersCardUserInfo()

def lambda_handler(event, context):
    logger.info(event)

    req_param = json.loads(event['body'])
    
    # idTokenを検証し、ユーザーIDを取得
    # https://developers.line.biz/ja/reference/line-login/#verify-id-token
    try:
        headers = {'Content-Type': 'application/x-www-form-urlencoded'}
        body = {
            'id_token': req_param['idToken'],
            'client_id': LIFF_CHANNEL_ID
        }
        response = requests.post(
            'https://api.line.me/oauth2/v2.1/verify',
            headers=headers,
            data=body
        )
        user_profile = json.loads(response.text)
        
        if 'error' in user_profile and 'expired' in user_profile['error_description']:  # noqa 501
            return utils.create_error_response('Forbidden', 403)
        else:
            req_param['userId'] = user_profile['sub']
            
    except Exception:
        logger.exception('不正なIDトークンが使用されています')
        return utils.create_error_response('Error')

    user_id = user_profile['sub']

    mode = req_param['mode']
    # modeによって振り分ける
    try:
        if mode == 'init':
            result = init(user_id)
        elif mode == 'buy':
            result = buy(user_id, req_param['language'], req_param['liffId'])

    except Exception as e:
        logger.error(e)
        return utils.create_error_response('ERROR')
    success_response = json.dumps(result,
                                  default=utils.decimal_to_int,
                                  ensure_ascii=False)
    return utils.create_success_response(success_response)


def init(user_id):
    """
    初期表示時、新規ユーザーの場合会員データを作成する。

    Parameters
    ----------
    user_id : str
        LINEのユーザーID

    Returns
    -------
    dict
        更新後のユーザー情報
    """
    
    # ユーザーデータ取得
    user_info = user_info_table_controller.get_item(user_id)
    
    # ログインユーザーのデータが無い場合、ユーザーデータを作成する
    if not user_info:
        barcode_num = random.randrange(10**12, 10**13)
    
        expiration_date = ''
        point = 0
        item = {
            'userId': user_id,
            'barcodeNum': barcode_num,
            'pointExpirationDate': expiration_date,
            'point': point,
        }
        # ユーザーデータ作成
        user_info_table_controller.put_item(
            user_id, barcode_num, expiration_date, point)
        
        return item

    return user_info


def buy(user_id, language, liffId):
    """
    商品を購入し、ポイント付与のDB更新と電子レシートの送信を行う。
    Parameters
    ----------
    user_id : str

    Returns
    -------
    dict
        更新後のユーザー情報

    """
    
    # 商品データ
    product_info = {
        "fee": 300,
        "postage": 0,
        "productName1": {
            "ja": "キャンバストートバッグ"
        },
        "productName2": {
            "ja": "デニムジャケット"
        },
        "unitPrice1": 21000,
        "unitPrice2": 13500
    }

    # 付与ポイントの取得
    user_info = user_info_table_controller.get_item(user_id)
    before_awarded_point = user_info['point']
    add_point = math.floor((product_info['unitPrice1'] * Decimal(0.05)) + (product_info['unitPrice2'] * Decimal(0.05))) #複数商品を出力するため
    after_awarded_point = before_awarded_point + add_point

    # 更新期限日の取得
    today = datetime.datetime.now(gettz('Asia/Tokyo'))
    expiration_date = (today + relativedelta(years=1)
                       ).strftime('%Y/%m/%d')

    # DB更新
    user_info_table_controller.update_point_expiration_date(
        user_id, after_awarded_point, expiration_date)

    user_info['pointExpirationDate'] = expiration_date
    user_info['point'] = after_awarded_point

    # メッセージ送信
    oa_channel_access_token = CHANNEL_ACCESS_TOKEN
    send_message.send_push_message(
        oa_channel_access_token, user_id, product_info, language, liffId)

    return user_info

