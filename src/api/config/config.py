class Config(object):
    DEBUG = False
    TESTING = False
    SQLALCHEMY_TRACK_MODIFICATIONS = False


class ProductionConfig(Config):
    SQLALCHEMY_TRACK_MODIFICATIONS = ''
    JSON_SORT_KEYS = False


class DevelopmentConfig(Config):
    DEBUG = True
    SQLALCHEMY_DATABASE_URI = 'mysql+mysqlconnector://root:tgof5569A@localhost:3306/testdb2'
    SQLALCHEMY_ECHO = False
    JSON_SORT_KEYS = False


class TestingConfig(Config):
    TESTING = True
    SQLALCHEMY_DATABASE_URI = ''
    SQLALCHEMY_ECHO = False
    JSON_SORT_KEYS = False
