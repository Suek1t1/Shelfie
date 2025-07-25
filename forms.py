from flask_wtf import FlaskForm
from wtforms.fields import (
    StringField, IntegerField, DateField, SubmitField, FileField, TextAreaField
)
from wtforms.validators import (
    DataRequired
)
from flask_wtf.file import (
    FileAllowed, FileRequired
)

# ==================================================
# Formクラス
# ==================================================
class UserInfoForm(FlaskForm):
    # 表紙、ページ画像：ファイルのアップロード
    img = FileField('画像: ', validators=[FileRequired('ファイルを選択してください。'), FileAllowed(['jpg', 'jpeg', 'png'], 'サポートされていない画像形式です。')
        ])
    # タイトル：文字列入力
    name = StringField('タイトル: ', validators=[DataRequired('タイトルを入力してください')])
    # 著者名：文字列入力
    author = StringField('著者名: ', validators=[DataRequired('著者名を入力してください')])
    # ISBNコード：整数値入力
    code = IntegerField('ISBNコード: ', validators=[DataRequired('ISBNコードを入力してください')])
    # 生年月日：日付入力
    add_date  = DateField('追加日: ', format="%Y-%m-%d", render_kw={"placeholder": "yyyy/mm/dd"}, validators=[DataRequired('追加日を入力してください')])
    # テキストエリア：自由記述
    note = TextAreaField('感想,メモ: ')
    # タグ：タグの追加（任意）
    tag = StringField('タグ(任意): ')
    # ボタン
    submit = SubmitField('完了')