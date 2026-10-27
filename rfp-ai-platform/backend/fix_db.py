import pymysql
try:
    conn = pymysql.connect(host='127.0.0.1', port=3306, user='root', password='sarvyanshu116611')
    cursor = conn.cursor()
    cursor.execute("CREATE DATABASE IF NOT EXISTS rfp_db;")
    cursor.execute("CREATE USER IF NOT EXISTS 'rfp_user'@'%' IDENTIFIED BY 'sarvyanshu116611';")
    cursor.execute("ALTER USER 'rfp_user'@'%' IDENTIFIED BY 'sarvyanshu116611';")
    cursor.execute("GRANT ALL PRIVILEGES ON rfp_db.* TO 'rfp_user'@'%';")
    cursor.execute("FLUSH PRIVILEGES;")
    conn.commit()
    conn.close()
    print('Root configuration successful')
except Exception as e:
    print('Root connection failed:', e)
    try:
        conn = pymysql.connect(host='127.0.0.1', port=3306, user='root', password='root')
        cursor = conn.cursor()
        cursor.execute("CREATE DATABASE IF NOT EXISTS rfp_db;")
        cursor.execute("CREATE USER IF NOT EXISTS 'rfp_user'@'%' IDENTIFIED BY 'sarvyanshu116611';")
        cursor.execute("ALTER USER 'rfp_user'@'%' IDENTIFIED BY 'sarvyanshu116611';")
        cursor.execute("GRANT ALL PRIVILEGES ON rfp_db.* TO 'rfp_user'@'%';")
        cursor.execute("FLUSH PRIVILEGES;")
        conn.commit()
        conn.close()
        print('Root (old password) configuration successful')
    except Exception as e2:
        print('Root (old password) connection failed:', e2)
