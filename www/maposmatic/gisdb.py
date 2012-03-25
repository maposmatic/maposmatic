import psycopg2
import www.settings

db = None

def get():
    global db
    if db:
        return db

    try:
        db = psycopg2.connect("dbname='%s' user='%s' host='%s' password='%s' port='%s'" %
                                (www.settings.GIS_DATABASE_NAME,
                                 www.settings.GIS_DATABASE_USER,
                                 www.settings.GIS_DATABASE_HOST,
                                 www.settings.GIS_DATABASE_PASSWORD,
                                 www.settings.GIS_DATABASE_PORT))
    except psycopg2.OperationalError, e:
        l.warning("Could not connect to the PostGIS database: %s" %
                  str(e)[:-1])
        return None

    return db
