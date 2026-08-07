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
