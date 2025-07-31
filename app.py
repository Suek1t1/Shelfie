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
    __tablename__ = "shelves"

    # 本棚ID
    shelf_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    book_id = db.Column(db.Integer, db.ForeignKey("books.book_id"), nullable=False)

    # リレーション
    book = db.relationship("Book", backref="shelves")

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


@app.route("/new", methods=["GET", "POST"])
def new_book():
    # フォームの作成
    form = UserInfoForm(request.form)
    # POST
    if request.method == "POST" and form.validate():
        # 入力値取得
        img = request.form["img"]
        name = request.form["name"]
        author = request.form["author"]
        add_date = request.form["add_date"]
        code = request.form["code"]
        memo = request.form["memo"]
        tag = request.form["tag"]
        # インスタンス生成
        book = Book(
            img=img,  # バイナリデータの場合は file.read() などで渡す
            name=name,
            author=author,
            add_date=add_date,  # 日付型ならdatetime型で渡す
            code=code,
            memo=memo,
            tag=tag,
        )
        # 登録
        db.session.add(book)
        db.session.commit()
        return redirect(url_for("index", form=form))
    # GET
    return render_template("new.html", form=form)


@app.route("/<int:book_id>/detail", methods=["GET"])
def book_detail(book_id):
    # 対象データ取得
    book = Book.query.get(book_id)
    return render_template("detail.html", book=book)


@app.route("/<int:book_id>/edit", methods=["GET", "POST"])
def edit(book_id):
    # 対象データ取得
    book = Book.query.get(book_id)
    # フォームの作成
    form = UserInfoForm(request.form)
    # POST
    if request.method == "POST" and form.validate():
        # 入力値取得
        img = request.form["img"]
        name = request.form["name"]
        author = request.form["author"]
        add_date = request.form["add_date"]
        code = request.form["code"]
        memo = request.form["memo"]
        tag = request.form["tag"]
        # 登録
        book.img = img
        book.name = name
        book.author = author
        book.add_date = add_date
        book.code = code
        book.memo = memo
        book.tag = tag
        # 反映
        db.session.commit()
        # 一覧へ
        return redirect(url_for("index", form=form))
    # GET
    return render_template("edit", form=form)


if __name__ == "__main__":
    app.run()
