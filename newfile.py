from flask import Flask, render_template_string, request, redirect, session, Response
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash

# ➕ TAMBAHAN QR CODE
import qrcode
import io
import base64
import uuid

app = Flask(__name__)
app.secret_key = "ABSENSI_FINAL_CLEAN"
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///absensi.db"
db = SQLAlchemy(app)

# ➕ TOKEN QR
qr_token = {}

# ================= DATABASE =================
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True)
    password = db.Column(db.String(200))
    nama = db.Column(db.String(100))
    kelas = db.Column(db.String(50))
    role = db.Column(db.String(20), default="siswa")

class Absensi(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nama = db.Column(db.String(100))
    kelas = db.Column(db.String(50))
    waktu = db.Column(db.String(50))

with app.app_context():
    db.create_all()

# ================= AUTH =================
@app.route("/", methods=["GET"])
def auth():
    return render_template_string("""
<!DOCTYPE html>
<html>
<head>
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Login</title>

<style>
body{
    margin:0;
    font-family:Arial;
    background:linear-gradient(135deg,#1d2b64,#f8cdda);
    height:100vh;
    display:flex;
    justify-content:center;
    align-items:center;
}

.box{
    width:340px;
    background:white;
    padding:25px;
    border-radius:15px;
    box-shadow:0 10px 25px rgba(0,0,0,0.2);
}

h1{
    text-align:center;
    color:#1d2b64;
    margin-bottom:0;
}

h3{
    text-align:center;
    margin-top:5px;
    color:#555;
}

input, select{
    width:100%;
    padding:10px;
    margin:5px 0;
    border-radius:8px;
    border:1px solid #ccc;
}

button{
    width:100%;
    padding:10px;
    border:none;
    border-radius:8px;
    color:white;
    cursor:pointer;
}

.login-btn{ background:#1d2b64; }
.register-btn{ background:#16a34a; }

.link{
    text-align:center;
    margin-top:10px;
    cursor:pointer;
    color:#1d4ed8;
}

.hidden{
    display:none;
}
</style>
</head>

<body>

<div class="box">

<h1>📚 PERPUSTAKAAN</h1>
<h3>SMKN 7 JAKARTA</h3>

<!-- LOGIN -->
<div id="loginBox">
    <h2 style="text-align:center;">Login</h2>

    <form method="post" action="/login">
        <input name="username" placeholder="Username" required>
        <input name="password" type="password" placeholder="Password" required>
        <button class="login-btn">Login</button>
    </form>

    <p class="link" onclick="showRegister()">Belum punya akun? Register</p>
</div>

<!-- REGISTER -->
<div id="registerBox" class="hidden">
    <h2 style="text-align:center;">Register</h2>

    <form method="post" action="/register">

        <input name="username" placeholder="Username" required>
        <input name="password" placeholder="Password" required>
        <input name="nama" placeholder="Nama" required>

        <select name="jurusan" id="jurusan" onchange="updateKelas()" required>
            <option value="">Pilih Jurusan</option>
            <option value="TKJ">TKJ</option>
            <option value="TG">TG</option>
            <option value="DKV">DKV</option>
        </select>

        <select name="kelas" id="kelas" required>
            <option value="">Pilih Kelas</option>
        </select>

        <select name="role" id="role" onchange="cekRole()">
            <option value="siswa">Siswa</option>
            <option value="guru">Guru</option>
        </select>

        <input name="kode" id="kode" placeholder="Kode Guru (0909)" style="display:none;">

        <button class="register-btn">Register</button>
    </form>

    <p class="link" onclick="showLogin()">Sudah punya akun? Login</p>
</div>

</div>

<script>
function showRegister(){
    document.getElementById("loginBox").classList.add("hidden");
    document.getElementById("registerBox").classList.remove("hidden");
}

function showLogin(){
    document.getElementById("registerBox").classList.add("hidden");
    document.getElementById("loginBox").classList.remove("hidden");
}

function cekRole(){
    var role = document.getElementById("role").value;
    document.getElementById("kode").style.display = (role=="guru") ? "block" : "none";
}

const dataKelas = {
    "TKJ": ["X TKJ 1","X TKJ 2","XI TKJ 1","XI TKJ 2","XII TKJ 1","XII TKJ 2"],
    "TG": ["X TG 1","X TG 2","X TG 3","XI TG 1","XI TG 2","XI TG 3","XI TG 4","XII TG 1","XII TG 2","XII TG 3","XII TG 4"],
    "DKV": ["X DKV 1","X DKV 2","X DKV 3","XI DKV 1","XI DKV 2","XII DKV 1","XII DKV 2"]
};

function updateKelas(){
    let jurusan = document.getElementById("jurusan").value;
    let kelasSelect = document.getElementById("kelas");

    kelasSelect.innerHTML = '<option value="">Pilih Kelas</option>';

    if(jurusan in dataKelas){
        dataKelas[jurusan].forEach(k => {
            let option = document.createElement("option");
            option.value = k;
            option.textContent = k;
            kelasSelect.appendChild(option);
        });
    }
}
</script>

</body>
</html>
""")

# ================= REGISTER =================
@app.route("/register", methods=["POST"])
def register():
    if User.query.filter_by(username=request.form["username"]).first():
        return "Username sudah dipakai"

    if request.form["role"] == "guru":
        if request.form.get("kode") != "0909":
            return "Kode guru salah!"

    db.session.add(User(
        username=request.form["username"],
        password=generate_password_hash(request.form["password"]),
        nama=request.form["nama"],
        kelas=request.form["kelas"],
        role=request.form["role"]
    ))
    db.session.commit()

    return redirect("/")

# ================= LOGIN =================
@app.route("/login", methods=["POST"])
def login():
    user = User.query.filter_by(username=request.form["username"]).first()

    if user and check_password_hash(user.password, request.form["password"]):
        session["user"] = user.username
        return redirect("/dashboard")

    return "Login gagal"

# ================= DASHBOARD =================
@app.route("/dashboard")
def dashboard():
    if "user" not in session:
        return redirect("/")

    from sqlalchemy import func

    user = User.query.filter_by(username=session["user"]).first()

    total_user = User.query.count()
    total_absen = Absensi.query.count()

    # ================= LEADERBOARD SISWA =================
    leaderboard = db.session.query(
        Absensi.nama,
        Absensi.kelas,
        func.count(Absensi.id).label("total")
    ).group_by(Absensi.nama).order_by(func.count(Absensi.id).desc()).limit(5).all()

    rows_siswa = ""
    rank = 1

    if leaderboard:
        for l in leaderboard:
            medal = "🥇" if rank == 1 else "🥈" if rank == 2 else "🥉" if rank == 3 else f"{rank}"
            highlight = "style='background:#fef9c3;'" if rank == 1 else ""

            rows_siswa += f"""
            <tr {highlight}>
                <td style="padding:8px;text-align:center;">{medal}</td>
                <td style="padding:8px;">{l.nama}</td>
                <td style="padding:8px;">{l.kelas}</td>
                <td style="padding:8px;text-align:center;"><b>{l.total}x</b></td>
            </tr>
            """
            rank += 1
    else:
        rows_siswa = "<tr><td colspan='4' style='text-align:center;'>Belum ada data</td></tr>"

    # ================= LEADERBOARD KELAS =================
    kelas_rank = db.session.query(
        Absensi.kelas,
        func.count(Absensi.id).label("total")
    ).group_by(Absensi.kelas).order_by(func.count(Absensi.id).desc()).limit(5).all()

    kelas_rows = ""
    rank_kelas = 1

    if kelas_rank:
        for k in kelas_rank:
            medal = "🥇" if rank_kelas == 1 else "🥈" if rank_kelas == 2 else "🥉" if rank_kelas == 3 else f"{rank_kelas}"
            highlight = "style='background:#dcfce7;'" if rank_kelas == 1 else ""

            kelas_rows += f"""
            <tr {highlight}>
                <td style="padding:8px;text-align:center;">{medal}</td>
                <td style="padding:8px;">{k.kelas}</td>
                <td style="padding:8px;text-align:center;"><b>{k.total}x</b></td>
            </tr>
            """
            rank_kelas += 1
    else:
        kelas_rows = "<tr><td colspan='3' style='text-align:center;'>Belum ada data</td></tr>"

    # ================= RANKING PRIBADI =================
    ranking_list = db.session.query(
        Absensi.nama,
        func.count(Absensi.id).label("total")
    ).group_by(Absensi.nama).order_by(func.count(Absensi.id).desc()).all()

    posisi = "-"
    total_user_absen = 0

    rank = 1
    for r in ranking_list:
        if r.nama == user.nama:
            posisi = rank
            total_user_absen = r.total
            break
        rank += 1

    if posisi == "-":
        posisi = "Belum masuk ranking"

    # ================= HTML =================
    return f"""
<html>
<head>
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Dashboard</title>
</head>

<body style="margin:0;font-family:Arial;background:#f4f6f9;">

<!-- HEADER -->
<div style="background:#111827;color:white;padding:15px;">
    <b>🏫 ABSENSI PERPUSTAKAAN</b>
    <a href="/logout" style="float:right;color:white;text-decoration:none;">Logout</a>
</div>

<!-- CONTENT -->
<div style="max-width:900px;margin:auto;padding:20px;">

<!-- CARD -->
<div style="display:flex;gap:15px;flex-wrap:wrap;">

<div style="flex:1;background:white;padding:20px;border-radius:12px;">
    <h3>👤 Profil</h3>
    <p><b>Nama:</b> {user.nama}</p>
    <p><b>Kelas:</b> {user.kelas}</p>
    <p><b>Role:</b> {user.role}</p>
</div>

<div style="flex:1;background:white;padding:20px;border-radius:12px;">
    <h3>📊 Statistik</h3>
    <p>👥 Total User: <b>{total_user}</b></p>
    <p>📌 Total Absen: <b>{total_absen}</b></p>
</div>

</div>

<!-- LEADERBOARD SISWA -->
<div style="margin-top:25px;background:white;padding:20px;border-radius:12px;">
<h3>🏆 Leaderboard Perpustakaan</h3>

<table style="width:100%;border-collapse:collapse;">
<tr style="background:#111827;color:white;">
    <th>Rank</th>
    <th>Nama</th>
    <th>Kelas</th>
    <th>Total Hadir</th>
</tr>
{rows_siswa}
</table>
</div>

<!-- LEADERBOARD KELAS -->
<div style="margin-top:25px;background:white;padding:20px;border-radius:12px;">
<h3>🏫 Kelas Terbanyak ke Perpustakaan</h3>

<table style="width:100%;border-collapse:collapse;">
<tr style="background:#111827;color:white;">
    <th>Rank</th>
    <th>Kelas</th>
    <th>Total Hadir</th>
</tr>
{kelas_rows}
</table>
</div>

<!-- RANKING PRIBADI -->
<div style="margin-top:20px;background:white;padding:20px;border-radius:12px;text-align:center;">
<h3>🎯 Ranking Kamu</h3>
<p style="font-size:20px;">
Posisi kamu: <b style="color:#1d4ed8;">{posisi}</b>
</p>
<p>Total hadir: <b>{total_user_absen}x</b></p>
</div>

<!-- MENU -->
<div style="margin-top:25px;">
<h3>🚀 Menu</h3>

<div style="display:flex;gap:10px;flex-wrap:wrap;">

<a href="/absen" style="flex:1;padding:12px;background:#1d2b64;color:white;border-radius:10px;text-align:center;text-decoration:none;">
📌 Absen
</a>

<a href="/preview" style="flex:1;padding:12px;background:#16a34a;color:white;border-radius:10px;text-align:center;text-decoration:none;">
📊 Preview
</a>

<a href="/data" style="flex:1;padding:12px;background:#0ea5e9;color:white;border-radius:10px;text-align:center;text-decoration:none;">
👥 Data
</a>

<a href="/export" style="flex:1;padding:12px;background:#f59e0b;color:white;border-radius:10px;text-align:center;text-decoration:none;">
📥 Export
</a>

{"<a href='/admin' style='flex:1;padding:12px;background:#ef4444;color:white;border-radius:10px;text-align:center;text-decoration:none;'>🔧 Admin</a>" if user.role=="guru" else ""}

{"<a href='/qr' style='flex:1;padding:12px;background:#8b5cf6;color:white;border-radius:10px;text-align:center;text-decoration:none;'>📷 QR Absen</a>" if user.role=="guru" else ""}

</div>
</div>

</div>
</body>
</html>
"""

# ================= ABSEN =================
@app.route("/absen", methods=["GET","POST"])
def absen():
    if "user" not in session:
        return redirect("/")

    user = User.query.filter_by(username=session["user"]).first()

    if request.method == "POST":
        db.session.add(Absensi(
            nama=user.nama,
            kelas=user.kelas,
            waktu=str(datetime.now())
        ))
        db.session.commit()
        return redirect("/preview")

    return f"""
    <body style="font-family:Arial;background:linear-gradient(120deg,#1d2b64,#f8cdda);display:flex;justify-content:center;align-items:center;height:100vh;">

    <div style="background:white;padding:30px;border-radius:15px;text-align:center;width:300px;">
        <h2>📌 ABSEN</h2>
        <p>{user.nama} - {user.kelas}</p>

        <form method="post">
            <button style="padding:10px;background:#1d2b64;color:white;border:none;border-radius:8px;">
                Absen
            </button>
        </form>
    </div>

    </body>
    """

# ================= QR ABSEN (TAMBAHAN BARU) =================
@app.route("/qr")
def qr():
    if "user" not in session:
        return redirect("/")

    user = User.query.filter_by(username=session["user"]).first()

    if user.role != "guru":
        return "❌ Hanya guru"

    token = str(uuid.uuid4())
    qr_token[token] = True

    link = f"http://10.16.6.243:5000/scan/{token}"

    img = qrcode.make(link)
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    img_str = base64.b64encode(buf.getvalue()).decode()

    return f"""
    <body style="text-align:center;font-family:Arial;">
        <h2>📌 QR ABSENSI</h2>
        <img src="data:image/png;base64,{img_str}" width="250">
        <p>Scan untuk absen</p>
    </body>
    """

# ================= SCAN QR =================
@app.route("/scan/<token>")
def scan(token):
    if "user" not in session:
        return redirect("/")

    user = User.query.filter_by(username=session["user"]).first()

    if token not in qr_token:
        return "❌ QR tidak valid / sudah expired"

    qr_token.pop(token)

    db.session.add(Absensi(
        nama=user.nama,
        kelas=user.kelas,
        waktu=str(datetime.now())
    ))
    db.session.commit()

    return f"""
    <h2>✅ Absen Berhasil</h2>
    <p>{user.nama} sudah tercatat</p>
    <a href="/dashboard">Kembali</a>
    """

# ================= PREVIEW =================
@app.route("/preview")
def preview():
    q = request.args.get("q","")
    filter_type = request.args.get("filter","today")

    today = datetime.now().strftime("%Y-%m-%d")
    bulan = datetime.now().strftime("%Y-%m")

    query = Absensi.query

    # ================= FILTER =================
    if filter_type == "today":
       query = query.filter(Absensi.waktu.like(f"{today}%"))
    elif filter_type == "month":
        query = query.filter(Absensi.waktu.like(f"{bulan}%"))

    # ================= SEARCH =================
    if q:
        query = query.filter(
            (Absensi.nama.like(f"%{q}%")) |
            (Absensi.kelas.like(f"%{q}%")) |
            (Absensi.waktu.like(f"%{q}%"))
        )

    data = query.all()

    rows = ""
    for d in data:
        rows += f"""
        <tr>
            <td>{d.nama}</td>
            <td>{d.kelas}</td>
            <td>{d.waktu}</td>
        </tr>
        """

    return f"""
<!DOCTYPE html>
<html lang="id">
<head>
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Preview Absensi</title>

<style>
body {{
    font-family: Arial;
    background: #f4f6f9;
    margin:0;
}}

.container {{
    max-width: 900px;
    margin: auto;
    padding: 20px;
}}

h1 {{
    text-align: center;
}}

.search-box {{
    text-align: right;
    margin-bottom: 15px;
}}

.search-box input {{
    padding: 10px;
    border-radius: 8px;
    border: 1px solid #ccc;
}}

.search-box button {{
    padding: 10px;
    border-radius: 8px;
    border: none;
    background: #1d2b64;
    color: white;
}}

.filter {{
    margin-bottom:10px;
}}

.filter a {{
    text-decoration:none;
    margin-right:10px;
    padding:6px 10px;
    background:#1d2b64;
    color:white;
    border-radius:6px;
}}

.card {{
    background: white;
    padding: 15px;
    border-radius: 12px;
    box-shadow: 0 4px 10px rgba(0,0,0,0.1);
}}

table {{
    width: 100%;
    border-collapse: collapse;
}}

thead {{
    background: #1d2b64;
    color: white;
}}

th, td {{
    padding: 12px;
}}

tbody tr:nth-child(even) {{
    background: #f9f9f9;
}}

tbody tr:hover {{
    background: #e0ecff;
}}

.back {{
    display:inline-block;
    margin-bottom:10px;
    text-decoration:none;
    color:white;
    background:#16a34a;
    padding:8px 12px;
    border-radius:8px;
}}
</style>
</head>

<body>

<div class="container">

<a href="/dashboard" class="back">⬅ Kembali</a>

<h1>📊 Preview Absensi</h1>

<!-- FILTER -->
<div class="filter">
    <a href="/preview?filter=today">Hari Ini</a>
    <a href="/preview?filter=month">Bulan Ini</a>
</div>

<div class="search-box">
<form>
    <input name="q" placeholder="Cari..." value="{q}">
    <button>Cari</button>
</form>
</div>

<div class="card">
<table>
<thead>
<tr>
    <th>Nama</th>
    <th>Kelas</th>
    <th>Waktu</th>
</tr>
</thead>

<tbody>
{rows}
</tbody>

</table>
</div>

</div>

</body>
</html>
"""

# ================= DATA USER =================
@app.route("/data")
def data():
    q = request.args.get("q","")

    if q:
        users = User.query.filter(
            (User.nama.like(f"%{q}%")) |
            (User.kelas.like(f"%{q}%")) |
            (User.role.like(f"%{q}%"))
        ).all()
    else:
        users = User.query.all()

    rows = ""
    for u in users:
        rows += f"<tr><td>{u.nama}</td><td>{u.kelas}</td><td>{u.role}</td></tr>"

    return f"""
    <body style="font-family:Arial;background:#f4f6f9;padding:20px;">

    <h2>👥 Data User</h2>

    <form>
        <input name="q" placeholder="Cari user..." style="padding:10px;width:300px;">
        <button>Cari</button>
    </form>

    <br>

    <table style="width:100%;background:white;">
    <tr style="background:#111827;color:white;">
        <th>Nama</th><th>Kelas</th><th>Role</th>
    </tr>
    {rows}
    </table>

    </body>
    """

# ================= EXPORT =================
@app.route("/export")
def export():
    data = Absensi.query.all()
    csv = "Nama,Kelas,Waktu\n"
    for d in data:
        csv += f"{d.nama},{d.kelas},{d.waktu}\n"

    return Response(csv, mimetype="text/csv",
        headers={"Content-Disposition":"attachment;filename=absensi.csv"})

# ================= ADMIN =================
@app.route("/admin")
def admin():
    if "user" not in session:
        return redirect("/")

    user_login = User.query.filter_by(username=session["user"]).first()

    # hanya guru (admin)
    if not user_login or user_login.role != "guru":
        return "❌ Akses ditolak"

    users = User.query.all()

    rows = ""
    for u in users:
        rows += f"""
        <tr>
            <td>{u.nama}</td>
            <td>{u.kelas}</td>
            <td>{u.role}</td>
            <td>
                <a href="/hapus_user/{u.id}" style="color:red;">Hapus</a>
            </td>
        </tr>
        """

    return f"""
<!DOCTYPE html>
<html>
<head>
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Admin</title>

<style>
body {{
    font-family:Arial;
    background:#f4f6f9;
    padding:20px;
}}

.card {{
    background:white;
    padding:20px;
    border-radius:12px;
    box-shadow:0 4px 10px rgba(0,0,0,0.1);
}}

table {{
    width:100%;
    border-collapse:collapse;
}}

th {{
    background:#111827;
    color:white;
    padding:10px;
}}

td {{
    padding:10px;
    border-bottom:1px solid #ddd;
}}

a {{
    text-decoration:none;
}}

.btn {{
    display:inline-block;
    padding:10px;
    background:#1d2b64;
    color:white;
    border-radius:8px;
    margin-bottom:10px;
}}
</style>
</head>

<body>

<a href="/dashboard" class="btn">⬅ Kembali</a>

<div class="card">
    <h2>🔧 ADMIN PANEL (GURU)</h2>

    <table>
        <tr>
            <th>Nama</th>
            <th>Kelas</th>
            <th>Role</th>
            <th>Aksi</th>
        </tr>
        {rows}
    </table>
</div>

</body>
</html>
"""

@app.route("/hapus_user/<int:id>")
def hapus_user(id):
    if "user" not in session:
        return redirect("/")

    user_login = User.query.filter_by(username=session["user"]).first()

    if not user_login or user_login.role != "guru":
        return "❌ Akses ditolak"

    user = User.query.get(id)

    if user:
        db.session.delete(user)
        db.session.commit()

    return redirect("/admin")

# ================= LOGOUT =================
@app.route("/logout")
def logout():
    session.clear()
    return redirect("/")

# ================= RUN =================


if __name__ == "__main__":
    import os
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)