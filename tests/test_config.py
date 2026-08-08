from app.config import Settings


def test_un_solo_origen_se_lee_como_lista_de_uno():
    config = Settings(frontend_origins="https://tallertrack.cl")

    assert config.origenes_permitidos == ["https://tallertrack.cl"]


def test_varios_origenes_separados_por_coma_se_leen_por_separado():
    config = Settings(frontend_origins="https://tallertrack.cl,http://localhost:3000")

    assert config.origenes_permitidos == ["https://tallertrack.cl", "http://localhost:3000"]


def test_los_espacios_alrededor_de_cada_origen_se_ignoran():
    config = Settings(frontend_origins=" https://tallertrack.cl , http://localhost:3000 ")

    assert config.origenes_permitidos == ["https://tallertrack.cl", "http://localhost:3000"]


def test_la_url_de_postgres_del_hosting_se_traduce_al_driver_instalado():
    """Railway entrega "postgresql://". Sin sufijo, SQLAlchemy busca psycopg2, que no
    esta instalado, y la aplicacion no levanta. El driver de este proyecto es psycopg 3.
    """
    config = Settings(database_url="postgresql://usuario:clave@servidor:5432/railway")

    assert config.database_url == "postgresql+psycopg://usuario:clave@servidor:5432/railway"


def test_tambien_se_traduce_la_forma_corta_postgres():
    """Algunos proveedores todavia entregan "postgres://", que SQLAlchemy ni siquiera acepta."""
    config = Settings(database_url="postgres://usuario:clave@servidor:5432/railway")

    assert config.database_url == "postgresql+psycopg://usuario:clave@servidor:5432/railway"


def test_una_url_que_ya_trae_su_driver_se_deja_como_esta():
    config = Settings(database_url="postgresql+psycopg://usuario:clave@servidor/db")

    assert config.database_url == "postgresql+psycopg://usuario:clave@servidor/db"


def test_la_url_de_sqlite_no_se_toca():
    config = Settings(database_url="sqlite:///./tallertrack.db")

    assert config.database_url == "sqlite:///./tallertrack.db"
