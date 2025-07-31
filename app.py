from flask import Flask, render_template, request, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.sql import func
from forms import UserInfoForm
from flask_migrate import Migrate
import os
from datetime import datetime

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
    # 本棚ID(外部キー)
    shelf_id = db.Column(
        db.Integer,
        db.ForeignKey("shelves.shelf_id", name="fk_book_shelf"),
        nullable=False,
    )

    # 表示用
    def __str__(self):
        return f"書籍ID：{self.id} 書籍名：{self.name}"


# 本棚
class Shelf(db.Model):
    # テーブル名
    __tablename__ = "shelves"

    # 本棚ID
    shelf_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    # book_id = db.Column(db.Integer, db.ForeignKey("books.book_id"), nullable=True)

    # リレーション
    books = db.relationship("Book", backref="shelf", lazy=True)

    # 表示用
    def __str__(self):
        return f"本棚ID：{self.shelf_id}"


# ==================================================
# ルーティング
# ==================================================


# 一覧
@app.route("/")
def index():
    # 本棚がなければ新しく作成
    if Shelf.query.first() is None:
        new_shelf = Shelf()
        db.session.add(new_shelf)
        db.session.commit()
    # 本を取得
    shelves = Shelf.query.all()
    books = Book.query.all()
    return render_template("index.html", shelves=shelves, books=books)


# 新規登録
@app.route("/new", methods=["GET", "POST"])
def new_book():
    # フォームの作成
    form = UserInfoForm()
    # POST
    if request.method == "POST" and form.validate_on_submit():
        # 入力値取得
        img_file = request.files["img"]
        img_data = img_file.read() if img_file else None
        name = form.name.data
        author = form.author.data
        add_date = datetime.now()  # 現在日時の設定
        code = form.code.data
        first_shelf = Shelf.query.first()
        # インスタンス生成
        book = Book(
            img=img_data,  # バイナリデータの場合は file.read() などで渡す→完了
            name=name,
            author=author,
            add_date=add_date,  # 日付型ならdatetime型で渡す→完了
            code=code,
            shelf_id=first_shelf.shelf_id,  # 紐づけ
        )
        # 登録
        db.session.add(book)
        db.session.commit()
        flash("登録が完了しました！", "success")
        return redirect(url_for("index", form=form))
    # GET
    return render_template("new.html", form=form)


# 詳細ページ
@app.route("/<int:book_id>/detail", methods=["GET"])
def book_detail(book_id):
    # 対象データ取得
    book = Book.query.get(book_id)
    return render_template("detail.html", book=book)


# 編集ページ
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
        code = request.form["code"]
        memo = request.form["memo"]
        tag = request.form["tag"]
        # 登録
        book.img = img
        book.name = name
        book.author = author
        book.code = code
        book.memo = memo
        book.tag = tag
        # 反映
        db.session.commit()
        # 一覧へ
        return redirect(url_for("index", form=form))
    # GET
    return render_template("edit", form=form)


# 実行
if __name__ == "__main__":
    app.run()
