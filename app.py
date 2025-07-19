from flask import Flask, render_template, request, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.sql import func
from forms import UserInfoForm
from flask_migrate import Migrate
import os

# ==================================================
# インスタンス生成
# ==================================================
app = Flask(__name__)

# ==================================================
# Flaskに対する設定
# ==================================================

# 乱数を設定
app.config["SECRET_KEY"] = os.urandom(24)
base_dir = os.path.dirname(__file__)
database = "sqlite:///" + os.path.join(base_dir, "data.sqlite")
app.config["SQLALCHEMY_DATABASE_URI"] = database
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

# ★db変数を使用してSQLAlchemyを操作できる
db = SQLAlchemy(app)
# ★「flask_migrate」を使用できる様にする
Migrate(app, db)


# ==================================================
# モデル
# ==================================================
# 書籍
class Book(db.Model):
    # テーブル名
    __tablename__ = "books"

    # 書籍ID
    book_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    # 書籍画像
    img = db.Column(db.LargeBinary, nullable=False)
    # 書籍の名前
    name = db.Column(db.String(255), nullable=False)
    # 著者名
    author = db.Column(db.String(50), nullable=False)
    # 書籍の追加日
    add_date = db.Column(db.DateTime(255), nullable=False, default=func.now())
    # ISBNコード
    code = db.Column(db.Integer, nullable=False)
    # メモ
    memo = db.Column(db.String(511))
    # タグ
    tag = db.Column(db.String(10))

    # 表示用
    def __str__(self):
        return f"書籍ID：{self.id} 書籍名：{self.name}"


# 本棚
class Shelf(db.Model):
    # テーブル名
    __tablename__ = "tasks"

    # 本棚ID
    shelf_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    book_id = db.Column(db.Integer, db.ForeignKey("books.book_id"), nullable=False)

    # 表示用
    def __str__(self):
        return f"本棚ID：{self.shelf_id}"


# ==================================================
# ルーティング
# ==================================================


@app.route("/")
def index():
    # 本を取得
    shelves = Shelf.query.all()
    books = Book.query.all()
    return render_template("index.html", shelves=shelves, books=books)


if __name__ == "__main__":
    app.run()
