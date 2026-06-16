from flask import Flask, render_template, request, redirect, url_for, session
import sqlite3

app = Flask(__name__)
app.secret_key = 'mucizevi_gizli_anahtar'

def veritabani_hazirla():
    baglanti = sqlite3.connect('veritabanı.db')
    cursor = baglanti.cursor()
    
    # 1. Bölümler Tablosu (sezon kolonu eklendi)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS bolumler (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            baslik TEXT NOT NULL,
            bolum_no INTEGER NOT NULL,
            link TEXT NOT NULL,
            aciklama TEXT,
            sezon TEXT NOT NULL
        )
    ''')
    
    # 2. Kullanıcılar Tablosu
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS kullanicilar (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            ad TEXT NOT NULL,
            eposta TEXT UNIQUE NOT NULL,
            sifre TEXT NOT NULL,
            rol TEXT DEFAULT 'user'
        )
    ''')
    
    try:
        cursor.execute('''
            INSERT INTO kullanicilar (ad, eposta, sifre, rol)
            VALUES (?, ?, ?, ?)
        ''', ('Admin Kutay', 'admin@mucizevi.com', '123456', 'admin'))
        baglanti.commit()
    except sqlite3.IntegrityError:
        pass
        
    baglanti.close()

veritabani_hazirla()

# --- ROTALAR ---

# 1. ANA SAYFA (Sezon filtresi alıyor)
@app.route('/')
def index():
    # Tarayıcıdan hangi sezonun istendiğini alıyoruz (Örn: /?sezon=1). Eğer seçilmediyse varsayılan "1" yapıyoruz.
    secilen_sezon = request.args.get('sezon', '1')
    
    baglanti = sqlite3.connect('veritabanı.db')
    cursor = baglanti.cursor()
    
    # Sadece seçilen sezona ait bölümleri getir
    cursor.execute('SELECT * FROM bolumler WHERE sezon = ? ORDER BY bolum_no ASC', (secilen_sezon,))
    sezon_bolumleri = cursor.fetchall()
    baglanti.close()
    
    return render_template('index.html', bolumler=sezon_bolumleri, aktif_sezon=secilen_sezon)

# 2. KAYIT OLMA
@app.route('/register', methods=['GET', 'POST'])
def register():
    hata = None
    if request.method == 'POST':
        ad = request.form['ad']
        eposta = request.form['eposta']
        sifre = request.form['sifre']
        
        baglanti = sqlite3.connect('veritabanı.db')
        cursor = baglanti.cursor()
        try:
            cursor.execute('INSERT INTO kullanicilar (ad, eposta, sifre, rol) VALUES (?, ?, ?, "user")', (ad, eposta, sifre))
            baglanti.commit()
            baglanti.close()
            return redirect(url_for('login'))
        except sqlite3.IntegrityError:
            hata = "Bu e-posta adresi zaten kayıtlı!"
            baglanti.close()
    return render_template('register.html', hata=hata)

# 3. GİRİŞ YAPMA
@app.route('/login', methods=['GET', 'POST'])
def login():
    hata = None
    if request.method == 'POST':
        eposta = request.form['eposta']
        sifre = request.form['sifre']
        
        baglanti = sqlite3.connect('veritabanı.db')
        cursor = baglanti.cursor()
        cursor.execute('SELECT * FROM kullanicilar WHERE eposta = ? AND sifre = ?', (eposta, sifre))
        kullanici = cursor.fetchone()
        baglanti.close()
        
        if kullanici:
            session['giriş_yapti'] = True
            session['kullanici_adi'] = kullanici[1]
            session['kullanici_rolu'] = kullanici[4]
            
            if kullanici[4] == 'admin':
                return redirect(url_for('admin_panel'))
            else:
                return redirect(url_for('index'))
        else:
            hata = "E-posta veya şifre hatalı! Giriş yapamazsınız."
    return render_template('login.html', hata=hata)

# 4. ADMIN PANELİ (Sezon seçimi eklendi)
@app.route('/admin', methods=['GET', 'POST'])
def admin_panel():
    if not session.get('giriş_yapti') or session.get('kullanici_rolu') != 'admin':
        return "Bu sayfaya erişim yetkiniz yok! Lütfen admin hesabı ile giriş yapın."
        
    if request.method == 'POST':
        baslik = request.form['baslik']
        bolum_no = request.form['bolum_no']
        link = request.form['link']
        aciklama = request.form['aciklama']
        sezon = request.form['sezon'] # HTML formundan gelen sezon bilgisi
        
        baglanti = sqlite3.connect('veritabanı.db')
        cursor = baglanti.cursor()
        cursor.execute('''
            INSERT INTO bolumler (baslik, bolum_no, link, aciklama, sezon) 
            VALUES (?, ?, ?, ?, ?)
        ''', (baslik, bolum_no, link, aciklama, sezon))
        baglanti.commit()
        baglanti.close()
        
        # Eklenen sezona ait sayfaya yönlendir ki kontrol edebilesin
        return redirect(url_for('index', sezon=sezon))
        
    return render_template('admin.html')

# 5. ÇIKIŞ
@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)