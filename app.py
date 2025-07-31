from flask import (
    Flask,
    render_template,
    request,
    redirect,
    url_for,
    flash,
    send_file,
    abort,
)
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.sql import func
from forms import UserInfoForm, EditBookForm
from flask_migrate import Migrate
import os
from datetime import datetime
import io

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
    # 感想、メモ
    note = db.Column(db.String(511))
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


# 書籍検索
@app.route("/search", methods=["GET", "POST"])
def search_book():
    # フォームの作成
    form = SearchBookForm()
    books = []  # 検索結果の格納

    if form.validate_on_submit():
        print("フォームは正常に送信されました。")
        search_word = form.search_word.data
        search_code = form.search_code.data

        if search_word:
            # タイトル(nameカラム)であいまい検索
            search_pattern = f"%{search_word}%"
            books = Book.query.filter(Book.name.like(search_pattern)).all()

        elif search_code:
            # ISBNコード(codeカラム)で完全一致検索
            books = Book.query.filter_by(code=search_code).all()

        # 結果をsearch_results.htmlに渡して表示
        return render_template("search_results.html", books=books)

    # GETリクエストの場合は検索フォームを表示
    return render_template("search.html", form=form)


# 詳細ページ
@app.route("/<int:book_id>/detail", methods=["GET", "POST"])
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
    form = EditBookForm(obj=book)
    # 編集画面で画像必須バリデータを外す
    form.img.validators = [
        v for v in form.img.validators if v.__class__.__name__ != "FileRequired"
    ]
    # POST
    if request.method == "POST" and form.validate_on_submit():
        # 入力値を登録
        img_file = request.files["img"]
        if img_file and img_file.filename:
            book.img = img_file.read()
        book.name = form.name.data
        book.author = form.author.data
        book.code = form.code.data
        book.note = form.note.data
        book.tag = form.tag.data
        # 反映
        db.session.commit()
        # 一覧へ
        return redirect(url_for("index", form=form))
    # GET
    return render_template("edit.html", form=form, book=book)


# 本の削除
@app.route("/<int:book_id>/delete", methods=["POST"])
def delete(book_id):
    # 対象データ取得
    book = Book.query.get(book_id)
    if book:
        db.session.delete(book)
        db.session.commit()
        flash("書籍を削除しました。", "success")
    else:
        flash("書籍が見つかりません。", "error")
    return redirect(url_for("index"))


# 画像URL作成
@app.route("/image/<int:book_id>/", methods=["GET"])
def serve_image(book_id):
    book = Book.query.get(book_id)
    if book and book.img:
        # 画像形式はpngのみ対応
        return send_file(
            io.BytesIO(book.img), mimetype="image/png", as_attachment=False
        )
    else:
        abort(404)


# 実行
if __name__ == "__main__":
    app.run()
