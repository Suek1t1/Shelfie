from flask_wtf import FlaskForm
from wtforms.fields import (
    StringField,
    IntegerField,
    SubmitField,
    FileField,
    TextAreaField,
)
from wtforms.validators import DataRequired
from flask_wtf.file import FileAllowed, FileRequired


# ==================================================
# Formクラス
# ==================================================
class UserInfoForm(FlaskForm):
    # 表紙、ページ画像：ファイルのアップロード
    img = FileField(
        "画像: ",
        validators=[
            FileRequired("ファイルを選択してください。"),
            FileAllowed(["jpg", "jpeg", "png"], "サポートされていない画像形式です。"),
        ],
    )
    # タイトル：文字列入力
    name = StringField(
        "タイトル: ", validators=[DataRequired("タイトルを入力してください")]
    )
    # 著者名：文字列入力
    author = StringField(
        "著者名: ", validators=[DataRequired("著者名を入力してください")]
    )
    # ISBNコード：整数値入力
    code = IntegerField(
        "ISBNコード: ", validators=[DataRequired("ISBNコードを入力してください")]
    )
    # テキストエリア：自由記述
    note = TextAreaField("備考: ")
    # ボタン
    submit = SubmitField("完了")
