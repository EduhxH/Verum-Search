"""Gera os ficheiros da marca a partir do desenho original.

O desenho chega como linhas brancas sobre fundo preto. A interface espera o
contrario - tinta escura sobre transparente - porque e o CSS que inverte a marca
quando o tema e escuro (`filter: invert(1)`), e assim ha um ficheiro em vez de
dois que depois ficam por actualizar.

A conversao e so uma troca de papeis: o **brilho** do original passa a ser a
**opacidade**, e a cor passa a ser uniforme. Os tons intermedios das bordas dos
tracos sobrevivem no canal alfa, portanto o contorno continua suave em vez de
serrilhado - que e o que aconteceria com um limiar simples.

    python scripts/gerar_marca.py                      # do original guardado
    python scripts/gerar_marca.py outro-desenho.png    # de outro ficheiro

Correr isto substitui os sete ficheiros de `assets/marca/`. O original fica em
`assets/marca/origem/`, para a marca se poder regenerar sem depender de nada
fora do repositorio.
"""

import sys
from pathlib import Path

from PIL import Image

RAIZ = Path(__file__).resolve().parent.parent
DESTINO = RAIZ / "assets" / "marca"
ORIGEM_GUARDADA = DESTINO / "origem" / "sigilo.png"

# Tinta de cada ficheiro. A da interface e preto puro porque o CSS a inverte
# para branco no tema escuro; a do PDF e do README e #111 e #fafafa, que sao as
# cores que o resto desses dois contextos ja usa.
TINTA_INTERFACE = (0, 0, 0)
TINTA_ESCURA = (17, 17, 17)
TINTA_CLARA = (250, 250, 250)

# Abaixo deste brilho e fundo, acima e traco; pelo meio e borda e fica em
# meio-tom. Os valores vem do proprio ficheiro: o fundo mede 13 e os tracos 255.
FUNDO_ATE = 40
TRACO_DESDE = 200

# Margem transparente a volta, em fraccao da altura. Sem ela o traco encosta a
# borda e o recorte do browser corta-lhe meio pixel.
MARGEM = 0.04

# nome -> (altura final, tinta, quadrado?)
# As alturas sao as dos ficheiros antigos, para nenhuma regra de CSS precisar de
# mudar: a marca do cabecalho e desenhada por altura, nao por largura.
FICHEIROS = {
    "gato.png": (390, TINTA_INTERFACE, False),
    "gato-fundo.png": (418, TINTA_INTERFACE, False),
    "404.png": (622, TINTA_INTERFACE, False),
    "icone.png": (32, TINTA_INTERFACE, True),
    "logo.png": (353, TINTA_ESCURA, False),
    "logo-branco.png": (353, TINTA_CLARA, False),
}


def extrair(origem: Path) -> Image.Image:
    """O desenho como tinta opaca sobre transparente, ja recortado."""
    cinzento = Image.open(origem).convert("L")

    escala = 255 / (TRACO_DESDE - FUNDO_ATE)
    tabela = [
        0 if v < FUNDO_ATE else (255 if v > TRACO_DESDE else int((v - FUNDO_ATE) * escala))
        for v in range(256)
    ]
    alfa = cinzento.point(tabela)

    caixa = alfa.getbbox()
    if caixa is None:
        raise SystemExit(f"{origem} nao tem desenho nenhum visivel")
    return alfa.crop(caixa)


def compor(alfa: Image.Image, altura: int, tinta, quadrado: bool) -> Image.Image:
    """Redimensiona e pinta. O alfa manda; a cor e uniforme por baixo."""
    margem = max(1, round(altura * MARGEM))
    util = altura - 2 * margem
    largura_util = max(1, round(util * alfa.width / alfa.height))

    reduzido = alfa.resize((largura_util, util), Image.LANCZOS)
    largura = altura if quadrado else largura_util + 2 * margem

    tela = Image.new("L", (largura, altura), 0)
    tela.paste(reduzido, ((largura - largura_util) // 2, margem))

    saida = Image.new("RGBA", tela.size, tinta + (0,))
    saida.putalpha(tela)
    return saida


def main() -> int:
    origem = Path(sys.argv[1]) if len(sys.argv) > 1 else ORIGEM_GUARDADA
    if not origem.exists():
        print(f"Nao encontrei o desenho: {origem}")
        return 1

    alfa = extrair(origem)
    print(f"desenho recortado: {alfa.width}x{alfa.height}")

    ORIGEM_GUARDADA.parent.mkdir(parents=True, exist_ok=True)
    if origem.resolve() != ORIGEM_GUARDADA.resolve():
        Image.open(origem).save(ORIGEM_GUARDADA)
        print(f"original guardado em {ORIGEM_GUARDADA.relative_to(RAIZ)}")

    for nome, (altura, tinta, quadrado) in FICHEIROS.items():
        imagem = compor(alfa, altura, tinta, quadrado)
        caminho = DESTINO / nome
        imagem.save(caminho, optimize=True)
        print(f"  {nome:<18} {imagem.width:>4}x{imagem.height:<4} "
              f"{caminho.stat().st_size // 1024:>3} KB")
    return 0


if __name__ == "__main__":
    sys.exit(main())
