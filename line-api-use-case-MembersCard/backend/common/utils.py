"""
共通関数
"""
from decimal import Decimal
from datetime import (datetime, timedelta)
import decimal
import os



def create_response(status_code, body):
    """
    フロントに返却するデータを作成する

    Parameters
    ----------
    status_code : int
        フロントに返却するステータスコード
    body:dict,str
        フロントに返却するbodyに格納するデータ
    Returns
    -------
    response : dict
        フロントに返却するデータ
    """
    response = {
        'statusCode': status_code,
        # 'headers': {"Access-Control-Allow-Origin": "*"},  # AWS CDK FunctionURLでCORS設定行うためコメントアウト
        'body': body
    }
    return response


def create_error_response(body, status=500):
    """
    エラー発生時にフロントに返却するデータを作成する

    Parameters
    ----------
    body : dict,str
        フロントに返却するbodyに格納するデータ
    status:int
        フロントに返却するステータスコード
    Returns
    -------
    create_response:dict
        フロントに返却するデータ
    """
    return create_response(status, body)


def create_success_response(body):
    """
    正常終了時にフロントに返却するデータを作成する

    Parameters
    ----------
    body : dict,str
        フロントに返却するbodyに格納するデータ
    Returns
    -------
    create_response:dict
        フロントに返却するデータ
    """
    return create_response(200, body)


def separate_comma(num):
    """
    数値を3桁毎のカンマ区切りにする

    Parameters
    ----------
    num : int
        カンマ区切りにする数値

    Returns
    -------
    result : str
        カンマ区切りにした文字列
    """
    return '{:,}'.format(num)


def decimal_to_int(obj):
    """
    Decimal型をint型に変換する。
    json形式に変換する際にDecimal型でエラーが出るため作成。
    主にDynamoDBの数値データに対して使用する。

    Parameters
    ----------
    obj : obj
        Decimal型の可能性があるオブジェクト

    Returns
    -------
    int, other
        Decimal型の場合int型で返す。
        その他の型の場合そのまま返す。
    """
    if isinstance(obj, Decimal):
        return int(obj)

