import os
import logging
import datetime
from dateutil.tz import gettz
import math
from decimal import Decimal
from linebot import LineBotApi
from linebot.models import FlexSendMessage
from linebot.exceptions import (
    LineBotApiError, InvalidSignatureError)
from common import utils

# 環境変数の宣言
LOGGER_LEVEL = os.getenv("LOGGER_LEVEL")

# ログ出力の設定
logger = logging.getLogger()
if LOGGER_LEVEL == 'DEBUG':
    logger.setLevel(logging.DEBUG)
else:
    logger.setLevel(logging.INFO)


def send_push_message(channel_access_token, user_id, product_obj, language, liffId):
    """
    プッシュメッセージを送信する

    Parameters
    ----------
    channel_access_token : str
        OAのチャネルアクセストークン
    user_id : str
        送信対象のユーザーID
    product_obj : dict
        データベースより取得した商品データ
    language : str
        多言語化対応用のパラメータ
    """
    logger.info('productObj: %s', product_obj)
    modified_product_obj = modify_product_obj(product_obj, language)

    flex_dict = make_flex_recept(**modified_product_obj, language=language, liffId=liffId)

    try:
        line_bot_api = LineBotApi(channel_access_token)
        # flexdictを生成する
        flex_dict = FlexSendMessage.new_from_json_dict(flex_dict)
        # push message 送信
        response = line_bot_api.push_message(user_id, flex_dict)
    except LineBotApiError as e:
        logger.error(
            'Got exception from LINE Messaging API: %s\n' % e.message)
        for m in e.error.details:
            logger.error('  %s: %s' % (m.property, m.message))
        raise Exception
    except InvalidSignatureError as e:
        logger.error('Occur Exception: %s', e)
        raise Exception
        
        
def modify_product_obj(product_obj, language, discount=0):
    """
    データベースより取得した商品データをメッセージ送信に適した状態のdict型に加工する

    Parameters
    ----------
    product_obj : dict
        データベースより取得した商品データ
    language : str
        多言語化対応用のパラメータ
    discount : int, optional
        値引き率。
        指定が無い場合0とする。

    Returns
    -------
    dict
        加工後の商品データ
    """
    now = datetime.datetime.now(
        gettz('Asia/Tokyo')).strftime('%Y/%m/%d %H:%M:%S')
    subtotal = product_obj['unitPrice1'] + product_obj['unitPrice2'] + \
        product_obj['postage'] + product_obj['fee'] - discount                  # 複数商品を出力するため
    tax = math.floor(subtotal * Decimal(0.10))
    total = subtotal + tax
    point = math.floor((product_obj['unitPrice1'] * Decimal(0.05)) + \
        (product_obj['unitPrice2'] * Decimal(0.05)))                            # 複数商品を出力するため
    logger.info('point: %s', point)
    modified_product_obj = {
        'date': now,
        'product_name1': product_obj['productName1'][language],                 # 複数商品を出力するため
        'product_name2': product_obj['productName2'][language],                 # 複数商品を出力するため
        'product_price1': utils.separate_comma(product_obj['unitPrice1']),      # 複数商品を出力するため
        'product_price2': utils.separate_comma(product_obj['unitPrice2']),      # 複数商品を出力するため
        'postage': utils.separate_comma(product_obj['postage']),
        'fee': utils.separate_comma(product_obj['fee']),
        'discount': utils.separate_comma(discount),
        'subtotal': utils.separate_comma(subtotal),
        'tax': utils.separate_comma(tax),
        'total': utils.separate_comma(total),
        'point': utils.separate_comma(point),
    }

    return modified_product_obj


def make_flex_recept(date, product_name1, product_name2, product_price1, product_price2, postage,
                     fee, discount, subtotal, tax, total,
                     point, language, liffId):
    """
    電子レシートのフレックスメッセージのdict型データを作成する

    Parameters
    ----------
    date: str
        yyyy/MM/dd hh:mm:ss形式の日付時刻
    product_name1: str      #複数商品を出力するため
        商品名
    product_name2: str      #複数商品を出力するため
        商品名
    product_price1: str     #複数商品を出力するため
        商品代金
    product_price2: str     #複数商品を出力するため
        商品代金
    postage: str
        送料
    commission: str
        手数料
    discount: str
        値下げ料
    subtotal: str
        小計
    tax: str
        消費税
    total: str
        合計
    point: str
        付与ポイント
    language: str
        言語設定

    Returns
    -------
    result : dict
        Flexmessageの元になる辞書型データ
    """
    return {
        "type": "flex",
        "altText": "お買い上げありがとうございます。電子レシートを発行します。",
        "contents": {
            "type": "bubble",
            "header": {
                "type": "box",
                "layout": "vertical",
                "contents": [
                    {
                        "type": "text",
                        "text": "Use Case STORE",
                        "size": "xxl",
                        "weight": "bold"
                    },
                    {
                        "type": "text",
                        "text": date,
                        "color": "#767676"
                    },
                    {
                        "type": "text",
                        "wrap": True,
                        "text": "※LINE API Use Caseサイトのデモアプリケーションであるため、実際の課金は行われません",
                        "color": "#ff6347"
                    }
                ]
            },
            "body": {
                "type": "box",
                "layout": "vertical",
                "contents": [
                    {
                        "type": "box",
                        "layout": "vertical",
                        "margin": "lg",
                        "spacing": "sm",
                        "contents": [
                            {
                                "type": "box",
                                "layout": "baseline",
                                "spacing": "sm",
                                "contents": [
                                    {
                                        "type": "text",
                                        "text": product_name1,
                                        "color": "#5B5B5B",
                                        "size": "sm",
                                        "flex": 5
                                    },
                                    {
                                        "type": "text",
                                        "text": product_price1,
                                        "wrap": True,
                                        "color": "#666666",
                                        "size": "sm",
                                        "flex": 2,
                                        "align": "end"
                                    }
                                ]
                            },
                            {
                                "type": "box",
                                "layout": "baseline",
                                "spacing": "sm",
                                "contents": [
                                    {
                                        "type": "text",
                                        "text": product_name2,
                                        "color": "#5B5B5B",
                                        "size": "sm",
                                        "flex": 5
                                    },
                                    {
                                        "type": "text",
                                        "text": product_price2,
                                        "wrap": True,
                                        "color": "#666666",
                                        "size": "sm",
                                        "flex": 2,
                                        "align": "end"
                                    }
                                ]
                            },
                            {
                                "type": "box",
                                "layout": "baseline",
                                "spacing": "sm",
                                "contents": [
                                    {
                                        "type": "text",
                                        "text": "送料（税抜）",
                                        "color": "#5B5B5B",
                                        "size": "sm",
                                        "flex": 5
                                    },
                                    {
                                        "type": "text",
                                        "text": postage,
                                        "wrap": True,
                                        "color": "#666666",
                                        "size": "sm",
                                        "flex": 2,
                                        "align": "end"
                                    }
                                ]
                            },
                            {
                                "type": "box",
                                "layout": "baseline",
                                "spacing": "sm",
                                "contents": [
                                    {
                                        "type": "text",
                                        "text": "決算手数料（税抜）",
                                        "color": "#5B5B5B",
                                        "size": "sm",
                                        "flex": 5
                                    },
                                    {
                                        "type": "text",
                                        "text": fee,
                                        "wrap": True,
                                        "color": "#666666",
                                        "size": "sm",
                                        "flex": 2,
                                        "align": "end"
                                    }
                                ]
                            },
                            {
                                "type": "box",
                                "layout": "baseline",
                                "spacing": "sm",
                                "contents": [
                                    {
                                        "type": "text",
                                        "text": "値引き",
                                        "color": "#5B5B5B",
                                        "size": "sm",
                                        "flex": 5
                                    },
                                    {
                                        "type": "text",
                                        "text": discount,
                                        "wrap": True,
                                        "color": "#666666",
                                        "size": "sm",
                                        "flex": 2,
                                        "align": "end"
                                    }
                                ]
                            },
                            {
                                "type": "box",
                                "layout": "baseline",
                                "spacing": "sm",
                                "contents": [
                                    {
                                        "type": "text",
                                        "text": "小計（税抜）",
                                        "color": "#5B5B5B",
                                        "size": "sm",
                                        "flex": 5
                                    },
                                    {
                                        "type": "text",
                                        "text": subtotal,
                                        "wrap": True,
                                        "color": "#666666",
                                        "size": "sm",
                                        "flex": 2,
                                        "align": "end"
                                    }
                                ]
                            },
                            {
                                "type": "box",
                                "layout": "baseline",
                                "spacing": "sm",
                                "contents": [
                                    {
                                        "type": "text",
                                        "text": "消費税",
                                        "color": "#5B5B5B",
                                        "size": "sm",
                                        "flex": 5
                                    },
                                    {
                                        "type": "text",
                                        "text": tax,
                                        "wrap": True,
                                        "color": "#666666",
                                        "size": "sm",
                                        "flex": 2,
                                        "align": "end"
                                    }
                                ]
                            },
                            {
                                "type": "box",
                                "layout": "baseline",
                                "spacing": "sm",
                                "contents": [
                                    {
                                        "type": "text",
                                        "text": "お会計金額",
                                        "color": "#5B5B5B",
                                        "size": "sm",
                                        "flex": 5
                                    },
                                    {
                                        "type": "text",
                                        "text": total,
                                        "wrap": True,
                                        "color": "#666666",
                                        "size": "sm",
                                        "flex": 2,
                                        "align": "end"
                                    }
                                ]
                            },
                            {
                                "type": "box",
                                "layout": "baseline",
                                "spacing": "sm",
                                "contents": [
                                    {
                                        "type": "text",
                                        "text": "付与ポイント",
                                        "color": "#5B5B5B",
                                        "size": "sm",
                                        "flex": 5
                                    },
                                    {
                                        "type": "text",
                                        "text": point,
                                        "wrap": True,
                                        "color": "#666666",
                                        "size": "sm",
                                        "flex": 2,
                                        "align": "end"
                                    }
                                ]
                            },
                        ],
                        "paddingBottom": "xxl"
                    },
                    {
                        "type": "box",
                        "layout": "vertical",
                        "contents": [
                            {
                                "type": "text",
                                "text": "商品のご購入ありがとうございます。\n本メッセージは、Use Case STOREおよびUse Case GROUPの店舗で商品をご購入されたお客様にお届けしています。",
                                "wrap": True,
                                "size": "sm",
                                "color": "#767676"
                            }
                        ]
                    }
                ],
                "paddingTop": "0%"
            },
            "footer": {
                "type": "box",
                "layout": "vertical",
                "spacing": "sm",
                "contents": [
                    {
                        "type": "button",
                        "style": "link",
                        "height": "sm",
                        "action": {
                            "type": "uri",
                            "label": "会員証を表示",
                            "uri": "https://liff.line.me/{liff_id}?lang={language}".format(liff_id=liffId, language=language)  # noqa: E501
                        },
                        "color": "#0033cc"
                    }
                ],
                "flex": 0
            }
        }
    }
    
    """
    廃止となった
    https://developers.line.biz/ja/news/2020/?month=10&day=08&article=flex-message-update-2-released#update-spacer
    {
        "type": "spacer",
        "size": "md"
    }
    """