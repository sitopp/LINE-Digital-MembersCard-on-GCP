"""
MembersCardUserInfo操作用モジュール

"""
import os
from datetime import datetime
from dateutil.tz import gettz
import firebase_admin
from firebase_admin import credentials
from firebase_admin import firestore


class MembersCardUserInfo:
    """MembersCardUserInfo操作用クラス"""
    __slots__ = ['_db']

    def __init__(self):
        """初期化メソッド"""
        cred = credentials.Certificate("./content/key.json")
        app = firebase_admin.initialize_app(cred)
        self._db = firestore.client()
    
    def put_item(self, user_id, barcode_num, expiration_date, point):
        """
        データ登録

        Parameters
        ----------
        user_id : str
            ユーザーID
        barcode_num : int
            バーコード番号
        expiration_date : str
            ポイント期限日
        point : int
            ポイント

        Returns
        -------
        response : dict
            レスポンス情報

        """
        item = {
            'userId': user_id,
            'barcodeNum': barcode_num,
            'pointExpirationDate': expiration_date,
            'point': point,
            'createdTime': datetime.now(
                gettz('Asia/Tokyo')).strftime("%Y/%m/%d %H:%M:%S"),
            'updatedTime': datetime.now(
                gettz('Asia/Tokyo')).strftime("%Y/%m/%d %H:%M:%S"),
        }

        try:
            doc_ref = self._db.collection('MembersCardUserInfo').document(user_id)
            doc_ref.set(item)
        except Exception as e:
            raise e        
        return {'result': 'success'}
       
    def update_point_expiration_date(self, user_id, point, expiration_date):
        """
        ポイントと期限日を更新する

        Parameters
        ----------
        user_id : str
            ユーザーID
        point : int
            ポイント
        expiration_date : str
            ポイント期限日

        Returns
        -------
        response : dict
            レスポンス情報

        """
        user_ref = self._db.collection('MembersCardUserInfo').document(user_id)
        try:
            response = user_ref.update({
                'point': point,
                'pointExpirationDate': expiration_date,
                'updatedTime': datetime.now(
                    gettz('Asia/Tokyo')).strftime("%Y/%m/%d %H:%M:%S")
            })
        except Exception as e:
            raise e
        return response
        
    def get_item(self, user_id):
        """
        データ取得

        Parameters
        ----------
        user_id : str
            ユーザーID

        Returns
        -------
        item : dict
            会員ユーザー情報

        """
        doc_ref = self._db.collection('MembersCardUserInfo').document(user_id)

        try:
            doc = doc_ref.get()
            if doc.exists:
                item = doc.to_dict()
            else:
                item = None
        except Exception as e:
            raise e
        return item