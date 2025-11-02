import sqlite3

def get_db_connection():
    """Membuat koneksi ke database."""
    conn = sqlite3.connect('tugas.db')
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    """Inisialisasi database dan tabel, lalu isi data matkul."""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS mata_kuliah (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nama TEXT NOT NULL,
        hari TEXT NOT NULL,
        jam TEXT NOT NULL,
        ruangan TEXT NOT NULL
    )
    ''')

    cursor.execute('''
    CREATE TABLE IF NOT EXISTS tugas (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        matkul_nama TEXT NOT NULL,
        deskripsi TEXT NOT NULL,
        deadline TEXT NOT NULL,
        status TEXT NOT NULL DEFAULT 'pending'
    )
    ''')
    
    cursor.execute("SELECT COUNT(*) FROM mata_kuliah")
    if cursor.fetchone()[0] == 0:
        # Isi 7 mata kuliah (contoh)
        matkul_default = [
            ('Kalkulus', 'Senin', '13:30 - 16:00', 'G3E'),
            ('Bahasa Indonesia', 'Selasa', '08:00 - 09:40', 'G3E'),
            ('Sistem Basis Data', 'Selasa', '10:45 - 13:15', 'Lab Programming'),
            ('Emerging Technologies & Digital Transformation', 'Selasa', '13:30 - 16:00', 'G1A'),
            ('Logika Informatika', 'Rabu', '08:00 - 10:30', 'G3A'),
            ('Algoritma Pemrograman', 'Rabu', '10:45 - 13:15', 'Lab Programming'),
            ('Sistem Operasi', 'Rabu', '16:00 - 18:00', 'Lab Programming')
            
        ]
        cursor.executemany(
            "INSERT INTO mata_kuliah (nama, hari, jam, ruangan) VALUES (?, ?, ?, ?)",
            matkul_default
        )
        print("Database diinisialisasi dan 7 mata kuliah ditambahkan.")
        
    conn.commit()
    conn.close()

def get_matkul():
    """Mengambil semua data mata kuliah, diurutkan berdasarkan hari dan jam."""
    conn = get_db_connection()
    cursor = conn.cursor()

    sql_query = """
    SELECT nama, hari, jam, ruangan
    FROM mata_kuliah
    ORDER BY
        CASE
            WHEN hari = 'Senin' THEN 1
            WHEN hari = 'Selasa' THEN 2
            WHEN hari = 'Rabu' THEN 3
            WHEN hari = 'Kamis' THEN 4
            WHEN hari = 'Jumat' THEN 5
            WHEN hari = 'Sabtu' THEN 6
            WHEN hari = 'Minggu' THEN 7
            ELSE 8
        END,
        jam
    """
    cursor.execute(sql_query)
    
    matkul = cursor.fetchall()
    conn.close()
    return matkul

def add_matkul(nama, hari, jam, ruangan):
    """Menambahkan mata kuliah baru ke database."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO mata_kuliah (nama, hari, jam, ruangan) VALUES (?, ?, ?, ?)",
        (nama, hari, jam, ruangan)
    )
    conn.commit()
    conn.close()

def delete_matkul(matkul_id):
    """Menghapus mata kuliah berdasarkan ID."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM mata_kuliah WHERE id = ?", (matkul_id,))
    conn.commit()
    conn.close()
    
def get_nama_matkul():
    """Hanya mengambil nama mata kuliah (untuk keyboard)."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT nama FROM mata_kuliah ORDER BY nama")

    nama_matkul = [row[0] for row in cursor.fetchall()]
    conn.close()
    return nama_matkul

def add_tugas(matkul, deskripsi, deadline):
    """Menambahkan tugas baru ke database."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO tugas (matkul_nama, deskripsi, deadline, status) VALUES (?, ?, ?, 'pending')",
        (matkul, deskripsi, deadline)
    )
    conn.commit()
    conn.close()

def get_tugas(status='pending'):
    """Mengambil semua tugas dengan status tertentu."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT id, matkul_nama, deskripsi, deadline FROM tugas WHERE status = ? ORDER BY deadline",
        (status,)
    )
    tugas = cursor.fetchall()
    conn.close()
    return tugas

def update_tugas_status(tugas_id, status):
    """Mengubah status tugas (cth: 'pending' -> 'done')."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("UPDATE tugas SET status = ? WHERE id = ?", (status, tugas_id))
    conn.commit()
    conn.close()

def delete_tugas(tugas_id):
    """Menghapus tugas berdasarkan ID."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM tugas WHERE id = ?", (tugas_id,))
    conn.commit()
    conn.close()

def clear_all_tugas():
    """Menghapus SEMUA tugas dari tabel."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM tugas")

    cursor.execute("DELETE FROM sqlite_sequence WHERE name='tugas'")
    conn.commit()
    conn.close()

if __name__ == '__main__':

    print("Menginisialisasi database...")
    init_db()
    print("Database 'tugas.db' siap.")