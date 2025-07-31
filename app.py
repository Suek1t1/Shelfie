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
from forms import UserInfoForm, EditBookForm, SearchBookForm
from flask_migrate import Migrate
import os
from datetime import datetime
import io

MAX_BOOKS_PER_SHELF = 16
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

    # 全ての本を取得
    books = Book.query.order_by(Book.book_id).all()
    # 必要な本棚数を計算
    shelf_count = Shelf.query.count()
    required_shelf_count = (len(books) + MAX_BOOKS_PER_SHELF - 1) // MAX_BOOKS_PER_SHELF

    # 足りない本棚を作成
    for _ in range(shelf_count, required_shelf_count):
        new_shelf = Shelf()
        db.session.add(new_shelf)
        db.session.commit()

    # 本棚リストをID昇順で取得
    shelves = Shelf.query.order_by(Shelf.shelf_id).all()

    # 本を本棚ごとに最大16冊ずつ振り分け直す
    for idx, book in enumerate(books):
        shelf_idx = idx // MAX_BOOKS_PER_SHELF
        if shelf_idx < len(shelves):
            if book.shelf_id != shelves[shelf_idx].shelf_id:
                book.shelf_id = shelves[shelf_idx].shelf_id
    db.session.commit()

    # 最新の状態で取得
    shelves = Shelf.query.order_by(Shelf.shelf_id).all()
    books = Book.query.order_by(Book.book_id).all()
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
        # 最新の本棚を取得
        last_shelf = Shelf.query.order_by(Shelf.shelf_id.desc()).first()
        if not last_shelf or len(last_shelf.books) >= MAX_BOOKS_PER_SHELF:
            # 新しい本棚を作成
            new_shelf = Shelf()
            db.session.add(new_shelf)
            db.session.commit()
            shelf_id = new_shelf.shelf_id
        else:
            shelf_id = last_shelf.shelf_id
        # インスタンス生成
        book = Book(
            img=img_data,
            name=name,
            author=author,
            add_date=add_date,
            code=code,
            shelf_id=shelf_id,  # 最新の本棚IDまたは新規本棚IDで紐づけ
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
    books = [] #検索結果の格納

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
        return render_template('search_results.html', books=books)

    # GETリクエストの場合は検索フォームを表示
    return render_template('search.html', form=form)


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
        book.memo = form.note.data
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
@app.route("/image/<int:book_id>/")
def serve_image(book_id):
    book = Book.query.get(book_id)
    if book and book.img:
        # 画像形式はpngのみ対応
        return send_file(
            io.BytesIO(book.img), mimetype="image/png", as_attachment=False
        )
    else:
        abort(404)


# 本棚を次に表示する用
@app.route("/<int:shelf_id>/move_to_next_shelf", methods=["POST"])
def move_to_next_shelf(shelf_id):
    # 現在の本棚IDの次の本棚を取得
    next_shelf = Shelf.query.filter(Shelf.shelf_id > shelf_id).order_by(Shelf.shelf_id).first()
    if next_shelf:
        flash(f"本棚{next_shelf.shelf_id}を表示します。", "success")
        return redirect(url_for("show_shelf", shelf_id=next_shelf.shelf_id))
    else:
        flash("次の本棚がありません。", "error")
        return redirect(url_for("show_shelf", shelf_id=shelf_id))

# 本棚ID指定で本棚を表示する
@app.route("/shelf/<int:shelf_id>")
def show_shelf(shelf_id):
    shelves = Shelf.query.order_by(Shelf.shelf_id).all()
    shelf = Shelf.query.get(shelf_id)
    return render_template("index.html", shelves=shelves, shelf=shelf)

# 前の本棚を表示する用
@app.route("/<int:shelf_id>/move_to_prev_shelf", methods=["POST"])
def move_to_prev_shelf(shelf_id):
    # 現在の本棚IDの前の本棚を取得
    prev_shelf = Shelf.query.filter(Shelf.shelf_id < shelf_id).order_by(Shelf.shelf_id.desc()).first()
    if prev_shelf:
        flash(f"本棚{prev_shelf.shelf_id}を表示します。", "success")
        return redirect(url_for("show_shelf", shelf_id=prev_shelf.shelf_id))
    else:
        flash("前の本棚がありません。", "error")
        return redirect(url_for("show_shelf", shelf_id=shelf_id))


# 実行
if __name__ == "__main__":
    app.run()
